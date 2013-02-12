import re
import lxml.html
from readability import readability

CONDENSE_WHITESPACE = re.compile('[^\S\n]+', re.UNICODE)
CONDENSE_NEWLINES = re.compile('\s*\n+\s*', re.UNICODE)


def condense_whitespace(string):
    
    #condense all whitespace (except newlines) to a single space
    string = re.sub(CONDENSE_WHITESPACE, ' ', string)

    #combine multiple newlines into one
    string = re.sub(CONDENSE_NEWLINES, '\n', string)

    return string


def readability_extract(response):
    """Takes an HTML string and returns text as (title, body)"""
    doc = readability.Document(response.encode('utf-8'))
    title_text = lxml.html.fromstring(doc.short_title()).text_content()
    body_text = render_text(lxml.html.fromstring(doc.summary()))
    body_text = standardize_quotes(body_text, "'", "'", '"', '"')
    return (condense_whitespace(title_text), condense_whitespace(body_text))

html_tags = set(['a', 'abbr', 'address', 'area', 'article', 'aside',
                 'audio', 'b', 'base', 'bdi', 'bdo', 'blockquote', 'body',
                 'br', 'button', 'canvas', 'caption', 'cite', 'code',
                 'col', 'colgroup', 'command', 'datalist', 'dd', 'del',
                 'details', 'dfn', 'div', 'dl', 'dt', 'em', 'embed',
                 'fieldset', 'figcaption', 'figure', 'footer', 'form',
                 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header',
                 'hgroup', 'hr', 'html', 'i', 'iframe', 'img', 'input',
                 'ins', 'kbd', 'keygen', 'label', 'legend', 'li', 'link',
                 'map', 'mark', 'menu', 'meta', 'meter', 'nav',
                 'noscript', 'object', 'ol', 'optgroup', 'option',
                 'output', 'p', 'param', 'pre', 'progress', 'q', 'rp',
                 'rt', 'ruby', 's', 'samp', 'script', 'section', 'select',
                 'small', 'source', 'span', 'strong', 'style', 'sub',
                 'summary', 'sup', 'table', 'tbody', 'td', 'textarea',
                 'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'track',
                 'u', 'ul', 'var', 'video', 'wbr'])
inline_tags = set(['a', 'abbr', 'acronym', 'b', 'basefont', 'bdo', 'big',
                   'br', 'cite', 'code', 'dfn', 'em', 'font', 'i', 'img',
                   'input', 'kbd', 'label', 'q', 's', 'samp', 'select',
                   'small', 'span', 'strike', 'strong', 'sub', 'sup',
                   'textarea', 'tt', 'u', 'var', 'applet', 'button',
                   'del', 'iframe', 'ins', 'map', 'object', 'script'])
block_tags = set(html_tags) - set(inline_tags)

def replace_nonstandard_tags(document):
    for e in document.iterdescendants():
        if not callable(e.tag) and e.tag not in html_tags:
            e.tag = 'span'

RELeftSingleQuotes = re.compile(ur'[\u2018\u201B]', re.UNICODE)
RERightSingleQuotes = re.compile(ur'[\u2019\u201A]', re.UNICODE)
RELeftDoubleQuotes = re.compile(ur'[\u201C\u201F]', re.UNICODE)
RERightDoubleQuotes = re.compile(ur'[\u201D]', re.UNICODE)

def standardize_quotes(text, leftsnglquot="'", rightsnglquot="'", leftdblquot='"', rightdblquot='"'):
    """Replaces fancy quotes from unicode, latin1, and windows-1252, defaulting to ascii quotes."""
    newtext = RELeftSingleQuotes.sub(leftsnglquot, text)
    newtext = RERightSingleQuotes.sub(rightsnglquot, newtext)
    newtext = RELeftDoubleQuotes.sub(leftdblquot, newtext)
    newtext = RERightDoubleQuotes.sub(rightdblquot, newtext)
    return newtext

def render_text(el, depth=0):
    """ like lxml.html text_content(), but with tactical use of whitespace for block elements """

    txt = u''
    if isinstance(el, lxml.html.HtmlComment):
        return txt

    tag = str(el.tag).lower()
    if tag in block_tags:
        txt += u"\n";

    if el.text is not None:
        txt += unicode(el.text)
    for child in el.iterchildren():
        txt += render_text(child, depth+1)
        if child.tail is not None:
            txt += unicode(re.sub('(\r\n|\n\r|\r|\n)', ' ', child.tail))

    if el.tag == 'br' or tag in block_tags:
        txt += u"\n";

    if depth == 0:
        txt = re.sub(r'[\r\n]\s+[\r\n]', '\n\n', txt)
        txt = re.sub(r'[\r\n]{2,}', '\n\n', txt)

    return txt


