/*
 jQuery Markdown editor
 derived from https://github.com/digitalnature/MarkdownEditor
 and https://github.com/jamiebicknell/Markdown-Helper
*/

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var csrftoken = getCookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function toLines(text, selection) {
    let lines = text.split('\n');
    let pos = 0;
    let start = null
    let end = null
    for (var line = 0; line < length(lines); line++) {
        if (start === null && pos + length(lines[line]) >= selection.start) {
            start = {line: line, pos: selection.start - pos}
        }
        if (pos + length(lines[line]) >= selection.end) {
            end = {line: line, pos: selection.end - pos}
            break;
        }
        pos = pos + length(lines[line]) + 1  // re-add the "/n" chars that
    }

    return {lines: lines, selection: {start: start, end: end}};
}

function length(str) {
    return str.length;
}

(function ($, window, document, undefined) {
    $.fn.MarkdownEditor = function (isFull) {

        var adjustOffset = function (input, offset) {
                let val = input.value, newOffset = offset;

                // adjust starting offset, because some browsers (like Opera) treat new lines as two characters (\r\n) instead of one character (\n)
                if (val.indexOf("\r\n") > -1) {
                    let matches = val.replace(/\r\n/g, "\n").slice(0, offset).match(/\n/g);
                    newOffset += matches ? matches.length : 0;
                }

                return newOffset;
            },

            // creates a selection inside the textarea
            // if selectionStart = selectionEnd the cursor is set to that point
            setCaretToPos = function (input, selectionStart, selectionEnd) {
                input.focus();

                if (input.setSelectionRange) {
                    input.setSelectionRange(adjustOffset(input, selectionStart), adjustOffset(input, selectionEnd));

                    // ie
                } else if (input.createTextRange) {
                    let range = input.createTextRange();
                    range.collapse(true);
                    range.moveEnd('character', selectionEnd);
                    range.moveStart('character', selectionStart);
                    range.select();
                }
            },

            tags = {
                bold: {
                    start: '**', end: '**', placeholder: 'Your bold text',
                    line: false, block: false
                },
                strike: {
                    start: '~~', end: '~~', placeholder: 'Your struckthrough text',
                    line: false, block: false
                },
                italic: {
                    start: '*', end: '*', placeholder: 'Your emphasized text',
                    line: false, block: false
                },
                h1: {
                    start: '# ', end: '', placeholder: 'Your header',
                    line: true, block: false
                },
                h2news: {
                    start: '## ', end: ' {.news-bg}', placeholder: 'Your header',
                    line: true, block: false
                },
                h3news: {
                    start: '### ', end: ' {.news-bg}', placeholder: 'Your header',
                    line: true, block: false
                },
                quote: {
                    start: '> ', end: '', placeholder: 'Your quote',
                    line: true, block: false
                },
                link: {
                    start: '[', end: '](https://example.org/)', placeholder: 'Add your link text',
                    line: false, block: false
                },
                image: {
                    start: '![', end: '](https://example.org/)', placeholder: 'Add image description',
                    line: false, block: false 
                },
                imageleft: {
                    start: '![', end: '](https://example.org/){.news-image-left}', placeholder: 'Add image description',
                    line: false, block: false
                },
                imageright: {
                    start: '![', end: '](https://example.org/){.news-image-right}', placeholder: 'Add image description',
                    line: false, block: false
                },
                code: {
                    start: '`', end: '`', placeholder: 'Add inline code here',
                    line: false, block: false
                },
                pre: {
                    start: '    ', end: '', placeholder: 'Block Code',
                    line: true, block: true
                },
                ul: {
                    start: '* ', end: '', placeholder: 'List Item',
                    line: true, block: true
                },
                ol: {
                    start: '1. ', end: '', placeholder: 'List Item',
                    line: true, block: true
                },
                break: {
                    start: '', end: '\n{.clearfix}', placeholder: '',
                    line: true, block: true
                },
                custom: {
                    start: '', end: ' {.custom-class-here}', placeholder: '',
                    line: true, block: true
                }
            };

        return this.each(function () {
            let txt = this,                          // textarea element
                stale = true,
                endpoint = $(this).data("endpoint") || "/api/md_preview/",
                controls = $('<div class="controls" id="' + txt.id + '-controls" />'); // button container
                stalePreviewIcon = 'fa-eye-slash'
                previewSource = controls;
            
            if (isFull) {
                previewSource = $('.full-preview');
                stalePreviewIcon = 'fa-check'
            }
            
            const format_classes = "btn btn-light";
            const button_template = '<button type="button" data-toggle="tooltip" data-placement="bottom" title="';
            var md_toolbar = '<div class="btn-toolbar" role="toolbar" aria-label="Markdown Toolbar">'
                + '<div class="btn-group mr-2 mb-1" role="group" aria-label="Formatting">'
                + button_template + 'Bold" class="' + format_classes + ' c-bold"><i class="fas fa-bold"></i></button>'
                + button_template + 'Italic" class="' + format_classes + ' c-italic"><i class="fas fa-italic"></i></button>'
                + button_template + 'Strikethrough" class="' + format_classes + ' c-strike"><i class="fas fa-strikethrough"></i></button>'
                + button_template + 'Code" class="' + format_classes + ' c-code"><i class="fas fa-code"></i></button>'

            if (!isFull) {
                md_toolbar += button_template + 'Heading" class="' + format_classes + ' c-h1"><i class="fas fa-heading"></i></button>'
            } else {
                md_toolbar += button_template + 'Heading 2" class="' + format_classes + ' c-h2news"><i class="fas fa-heading"></i>2</button>'
                    + button_template + 'Heading 3" class="' + format_classes + ' c-h3news"><i class="fas fa-heading"></i>3</button>'
            }

            md_toolbar += button_template + 'Quote" class="' + format_classes + ' c-quote"><i class="fas fa-quote-right"></i></button>'

                + '</div><div class="btn-group mr-2 mb-1" role="group" aria-label="Utilities">'
                + button_template + 'Link" class="' + format_classes + ' c-link"><i class="fas fa-link"></i></button>'
                + button_template + 'Image" class="' + format_classes + ' c-image"><i class="fas fa-image"></i></button>'
            
            if (isFull) {
                md_toolbar += button_template + 'Image (Left, 50% Width)" class="' + format_classes + ' c-imageleft"><i class="fas fa-caret-left"></i>&nbsp;<i class="fas fa-image"></i></button>'
                    + button_template + 'Image (Right, 50% Width)" class="' + format_classes + ' c-imageright"><i class="fas fa-image"></i>&nbsp;<i class="fas fa-caret-right"></i></button>'
            }

            md_toolbar += '</div><div class="btn-group mr-2 mb-1" role="group" aria-label="Lists">'
                + button_template + 'Bullet List" class="' + format_classes + ' c-ul"><i class="fas fa-list-ul"></i></button>'
                + button_template + 'Ordered List" class="' + format_classes + ' c-ol"><i class="fas fa-list-ol"></i></button>'

            if (isFull) {
                // TODO: add ? button with a classes reference.
                md_toolbar += '</div><div class="btn-group mr-2 mb-1" role="group" aria-label="Classes">'
                    + button_template + 'Section Break" class="' + format_classes + ' c-break"><i class="fas fa-level-down-alt"></i></button>'
                    + button_template + 'Custom Class" class="' + format_classes + ' c-custom"><i class="fas fa-hammer"></i></button>'
            }

            md_toolbar += '</div><div class="btn-group mr-2 mb-1" role="group" aria-label="Preview">'
                + button_template + 'Preview" class="' + format_classes + ' c-preview"><i class="fas fa-eye"></i></button>'
                + '</div>'
                + '</div>'
 
            if (!isFull) md_toolbar += '<div class="preview"></div>'

            let doPreview = function() {
                if (stale) {
                    stale = false;
                    controls.find('.fa-eye').removeClass('fa-eye').addClass(stalePreviewIcon);
                    createPreview(txt, previewSource, endpoint);
                } else {
                    if (!isFull) previewSource.find('.preview').slideUp();
                    controls.find('.'+stalePreviewIcon).removeClass(stalePreviewIcon).addClass('fa-eye');
                    stale = true;
                }
                return true;
            };
            let timeout;
            if (isFull) timeout = setTimeout(doPreview, 1);

            $(txt).before(controls.append(md_toolbar));
            if (!isFull) controls.find('.preview').slideUp();
            $(txt).on('keydown', function (event) {
                previewSource.find('.card').addClass("text-muted");
                controls.find('.'+stalePreviewIcon).removeClass(stalePreviewIcon).addClass('fa-eye');
                stale = true;
                if (isFull) {
                    clearTimeout(timeout);
                    timeout = setTimeout(doPreview, 600);
                }
                return MarkdownHelper(txt, event);
            });

            $('button', controls).on('click', function (event) {
                event.preventDefault();
                txt.focus();

                let tagName = this.className.substr(format_classes.length + 3),
                    range = {start: txt.selectionStart, end: txt.selectionEnd};
                let tag = tags[tagName]

                if (tagName === "preview") {
                    return doPreview();
                }
                let a = toLines(txt.value, range);
                let lines = a.lines;
                let selection = a.selection;

                if (tag === tags.code && selection.start.line !== selection.end.line) {
                    tag = tags.pre;  // Code button changes behaviour in multi-line mode
                }

                let start_delta = 0, end_delta = 0;
                if (tag.line) {
                    if (selection.start.line === selection.end.line && lines[selection.start.line] === "") {

                        lines[selection.start.line] = tag.start + tag.placeholder + tag.end;
                        end_delta += length(lines[selection.start.line]);
                    } else {
                        start_delta += length(tag.start);
                        for (let i = selection.start.line; i <= selection.end.line; i++) {
                            lines[i] = tag.start + lines[i] + tag.end;
                            end_delta += length(tag.start);
                        }
                    }
                } else {
                    if (range.start !== range.end) {
                        lines[selection.end.line] = lines[selection.end.line].substring(0, selection.end.pos) + tag.end + lines[selection.end.line].substring(selection.end.pos);
                        lines[selection.start.line] = lines[selection.start.line].substring(0, selection.start.pos) + tag.start + lines[selection.start.line].substring(selection.start.pos);
                        start_delta += length(tag.start);
                        end_delta += length(tag.start);
                    } else {
                        lines[selection.start.line] = lines[selection.start.line].substring(0, selection.start.pos) + tag.start + tag.placeholder + tag.end + lines[selection.start.line].substring(selection.start.pos);
                        start_delta += length(tag.start);
                        end_delta += length(tag.start + tag.placeholder);
                    }
                }

                if (tag.block && (selection.start.line - 1) >= 0 && lines[selection.start.line - 1] !== "") {
                    lines[selection.start.line] = "\n" + lines[selection.start.line];
                    start_delta += 1;
                }
                if (tag.block && (selection.end.line + 1) <= lines.length && lines[selection.end.line + 1] !== "") {
                    lines[selection.end.line] = lines[selection.end.line] + "\n";
                }
                txt.value = lines.join("\n");
                setCaretToPos(txt, range.start + start_delta, range.end + end_delta);

                stale=true;
                previewSource.find('.card').addClass("text-muted");
                controls.find('.'+stalePreviewIcon).removeClass(stalePreviewIcon).addClass('fa-eye');
                if (isFull) {
                    clearTimeout(timeout);
                    timeout = setTimeout(doPreview, 600);
                }

                return true;
            });

        });

    };

})(jQuery, window, document);

function createPreview(txt, controls, endpoint) {
    $.post(endpoint, {'md': txt.value}, function (data, status, jqXHR) {
        controls.find('.preview').html(data).slideDown();
    });
}

function MarkdownHelper(block, event) {
    let check, input, start, range, lines, state, value, first, prior, label, begin, width, caret;
    if (event.keyCode === 13) {
        check = false;
        input = block.value.replace(/\r\n/g, '\n');
        if (block.selectionStart) {
            start = block.selectionStart;
        } else {
            block.focus();
            range = document.selection.createRange();
            range.moveStart('character', -input.length);
            start = range.text.replace(/\r\n/g, '\n').length;
        }
        lines = input.split('\n');
        state = input.substr(0, start).split('\n').length;
        value = lines[state - 1].replace(/^\s+/, '');
        first = value.substr(0, 2);
        if (new RegExp('^[0-9]+[.] (.*)$').test(value)) {
            prior = value.substr(0, value.indexOf('. '));
            begin = prior + '. ';
            label = (parseInt(prior, 10) + 1) + '. ';
            check = true;
        }
        if (value && !check && lines[state - 1].substr(0, 4) === '    ') {
            begin = label = '    ';
            check = true;
        }
        if (['* ', '+ ', '- '].indexOf(first) >= 0) {
            begin = label = first;
            check = true;
        }
        if (check) {
            width = lines[state - 1].indexOf(begin);
            if (value.replace(/^\s+/, '') === begin) {
                block.value = input.substr(0, start - 1 - width - label.length) + '\n\n' + input.substr(start, input.length);
                caret = start + 1 - label.length - width;
            } else {
                block.value = input.substr(0, start) + '\n' + (new Array(width + 1).join(' ')) + label + input.substr(start, input.length);
                caret = start + 1 + label.length + width;
            }
            if (block.selectionStart) {
                block.setSelectionRange(caret, caret);
            } else {
                range = block.createTextRange();
                range.move('character', caret);
                range.select();
            }
            return false;
        }
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}