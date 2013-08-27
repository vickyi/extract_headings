#!/usr/bin/env python

from HTMLParser import HTMLParser
from pelican import signals, readers, contents
import os, re, markdown
from markdown.extensions import headerid

def my_slugify(value, separator):
    return "toc_{}".format(value.encode("hex"))

class Heading:
    HeadRegex = re.compile("h[1-6]")
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def __repr__(self):
        return "{}:{}".format(self.tag, self.value)

    @classmethod
    def is_heading(cls, tag):
        return None != cls.HeadRegex.match(tag)

class HeadingParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.headings = []
        self.tagOpen = False

    def handle_starttag(self, tag, attrs):
        if Heading.is_heading(tag):
            self.headings.append(Heading(tag, ""))
            self.tagOpen = True

    def handle_endtag(self, tag):
        self.tagOpen = False

    def handle_data(self, data):
        if self.tagOpen and len(self.headings) > 0:
            self.headings[-1].value = data

def extract_headings(content):
    if isinstance(content, contents.Static):
        return

    markdownFilePath = content.source_path
    extension = os.path.splitext(markdownFilePath)[1][1:]
    if not extension in readers.MarkdownReader.file_extensions:
        return

    htmlContent = markdown.markdown(content._content, extensions=['headerid(forceid=False)'])
    parser = HeadingParser()
    parser.feed(htmlContent)
    content.html_headings = parser.headings
    # set article title to h1 if any
    content.html_h1 = ""
    for head in parser.headings:
        if "h1" == head.tag:
            content.html_h1 = head.value
        if not content.html_h1:
            content.html_h1 = content.title
    # set article toc
    content.html_toc = "<ul>"
    prevHead = None
    openListSetNum = 0
    linkFormat = "<a href='#{}'>{}</a>"
    #linkFormat = ""
    for i in xrange(len(parser.headings)):
        head = parser.headings[i]
        head.parent = None
        headID = headerid.slugify(head.value, "-")
        # first elem
        if 0 == i:
            content.html_toc += ("<li>" + linkFormat).format(headID, head.value)
            continue
        prevHead = parser.headings[i-1]
        if head.tag > prevHead.tag:
            head.parent = prevHead
            openListSetNum += 1
            content.html_toc += ("<ul><li>" + linkFormat).format(headID, head.value)
        elif head.tag < prevHead.tag:
            currParent = prevHead.parent
            while currParent and (head.tag <= currParent.tag):
                openListSetNum -= 1
                content.html_toc += ("</li></ul>")
                currParent = currParent.parent
            head.parent = currParent
            content.html_toc += ("</li><li>" + linkFormat).format(headID, head.value)
        else:
            head.parent = prevHead.parent
            content.html_toc += ("</li><li>" + linkFormat).format(headID, head.value)

    while openListSetNum > 0:
        content.html_toc += ("</li></ul>")
        openListSetNum -= 1
    if len(parser.headings) > 1:
        content.html_toc += "</li></ul>"
    else:
        content.html_toc += "</ul>"

def register():
    signals.content_object_init.connect(extract_headings)

if __name__ == "__main__":
    parser = H1Parser()
    htmlStr = open("./index.html").read()
    parser.feed(htmlStr)
    print parser.h1

