#  -*- coding: utf-8 -*-
#  FileHeader.py ---
#  created: 2012-03-06 09:29:02
#


"""
Sublime Text 2 Plugin to generate file headers.
"""


import re
from os import path
from functools import partial
from datetime import datetime
import sublime
import sublime_plugin


# define your header
# todo: this should be done in project/sublime settings
header = [
    '-*- coding: utf-8 -*-',
    '$filename ---',
    'created: $timestamp',
    ' ',
    '',
    '',
]

# define your footer
# todo: this should be done in project/sublime settings
footer = [
    '',
    ' ',
    '$filename ends here',
    '',
]

# list all supported keywords
# todo: keywords should be defined as list and this regex generated
keywords = r'(?P<key>\$filename|\$timestamp|\$\$)'


class FileHeaderCommand(sublime_plugin.TextCommand):
    """ Command to generate file header. """

    def __init__(self, view):
        """ Define mappings. """
        super(FileHeaderCommand, self).__init__(view)
        self.key_mappings = {
            '$timestamp': lambda : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '$filename': self.filename,
            '$$': lambda : '$',
        }

    def run(self, edit):
        """ Generate header and footer. """
        newl, comm = self._get_newline_and_comment(0)

        hdr = self._generate_comments(header, newl, comm)
        ftr = self._generate_comments(footer, newl, comm)
        self._write_comments(hdr, 0, edit)
        self._write_comments(ftr, self.view.size(), edit)

    def filename(self):
        """ Return the name of the file.

        :returns: name of the file or empty if the buffer isn't saved yet.
        """

        name = self.view.file_name()
        if not name:
            return ''
        else:
            return path.basename(name)

    def _generate_comments(self, lines, newline, comment):
        """ Generate file header or footer. """
        # calculate number of empty lines (i.e. no comment character)
        empties_pre = self._empty_count(lines)
        empties_post = self._empty_count(reversed(lines))
        # generate comment lines
        comment_lines = self._render_comments(
            lines[empties_pre:(len(lines) - empties_post)], comment)
        # add empty lines
        empties_pre = ['' for i in range(empties_pre)]
        empties_post = ['' for i in range(empties_post)]
        comment_lines = empties_pre + comment_lines + empties_post
        # convert to string and return
        return self._comments_to_string(comment_lines, newline)

    def _write_comments(self, comment, point, edit):
        self.view.insert(edit, point, comment)

    def _get_newline_and_comment(self, point):
        """ Return newline and comment character.

        todo: newline should be checked from settings (unix / windows)
        :returns: tuple consisting newline and comment character
        """

        shell_vars = self.view.meta_info("shellVariables", point)
        shell_vars = dict([(shv['name'], shv['value']) for shv in shell_vars])
        return (
            '\n',
            shell_vars['TM_COMMENT_START'],
            )

    def _keyword_replacer(self, match):
        """ Replaces a single keyword in the comment.

        This function is to be used in conjunction with the regex
        substituter. The keyword is looked up in `self.key_mappings`
        and corresponding replacer function is executed. If the
        keyword is unknown, returns the same keyword back.

        :param match: the match object returned by the regex
                      that matched the keyword.
        :returns: the string generated
        """

        for key, value in match.groupdict().items():
            try:
                replacer = self.key_mappings[value]
            except KeyError:
                # unknown keyword, return it back
                return match.string[match.start():match.end()]
            else:
                # known keyword -> apply
                return replacer()

    def _render_comment(self, line):
        """ Execute the regex to replace keywords on the given line. """
        line = re.sub(
            keywords,
            self._keyword_replacer,
            line)
        return line

    def _render_comments(self, lines, comment_mark):
        """ Call `_render_comment` for each line. """
        lines = map(self._render_comment, lines)
        return ['%s %s' % (comment_mark, line) for line in lines]

    def _empty_count(self, comment_list):
        """ Calculate the number of empty lines in the beginning. """
        empties = 0
        for line in comment_list:
            if line == '':
                empties += 1
            else:
                break
        return empties

    def _comments_to_string(self, comment_list, newl):
        """ Convert list of comment lines into one string. """
        return newl.join(comment_list)

#
#  FileHeader.py ends here
