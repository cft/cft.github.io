#!/usr/bin/env python3
"""
CREATE TABLE `audio` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `podcast` tinyint(1) NOT NULL DEFAULT '0',
  `book` varchar(255) NOT NULL,
  `chapter` text NOT NULL,
  `title` varchar(255) NOT NULL,
  `hi_fi` varchar(255) NOT NULL,
  `lo_fi` varchar(255) NOT NULL,
  `pubdate` date NOT NULL,
  `keywords` text NOT NULL,
  `description` text NOT NULL,
  `img` varchar(255) NOT NULL,
  `img_credit` varchar(255) NOT NULL,
  `order` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

  (119,1,'Mark','1:14-45','Why People Came to Jesus','why_people_came_to_jesus.mp3','why_people_came_to_jesus_lo.mp3','2007-08-19','','Jesus calls his 12 disciples; why did they respond?  At Capernaum, demons are cast out and Jesus heals people.','','',10),

"""
import csv
import json
import os
import re
import shutil
import sys


LINE_RE = re.compile(
  r"\((?P<id>\d+),"
  r"(?P<podcast>\d+),"
  r"(?<!\\)'(?P<book>.*)(?<!\\)',"
  r"(?<!\\)'(?P<chapter>.*)(?<!\\)',"
  r"(?<!\\)'(?P<title>.*)(?<!\\)',"
  r"(?<!\\)'(?P<hi_fi>.*)(?<!\\)',"
  r"(?<!\\)'(?P<lo_fi>.*)(?<!\\)',"
  r"(?<!\\)'(?P<pubdate>.*)(?<!\\)',"
  r"(?<!\\)'(?P<keywords>.*)(?<!\\)',"
  r"(?<!\\)'(?P<description>.*)(?<!\\)',"
  r"(?<!\\)'(?P<img>.*)(?<!\\)',"
  r"(?<!\\)'(?P<img_credit>.*)(?<!\\)',"
  r"(?P<order>\d+)\)[,;]$"
)


def remove_crap(s):
  s = re.sub(r'(\\r\\n|\\r|\\n)', ' ', s)
  s = re.sub(r'(’|\\\')', '\'', s)
  s = re.sub(r'\\"', '"', s)
  s = re.sub(r'(&amp;)', '&', s)
  return s.strip()


def main(filename, out_dir, mp3_dir):
  if not os.path.exists(out_dir):
    os.mkdir(out_dir)

  index_csv = os.path.join(out_dir, 'index.csv')

  with open(index_csv, 'w', newline='') as out_f:
    out_csv = csv.writer(out_f)
    out_csv.writerow(['book_slug', 'order_in_book', 'chapter_slug', 'title_slug', 'book', 'chapter', 'title', 'description', 'keywords', 'mp3_file', 'description_txt_file', 'json_file'])

    rows = []

    with open(filename) as f:
      for line in f:
        line = line.strip()
        if not line:
          continue
        ma = LINE_RE.match(line)
        if not ma:
          raise ValueError(line)
        
        book = remove_crap(ma.group('book').strip())
        book_slug = re.sub(r'\s+', '-', book.lower())

        chapter = remove_crap(ma.group('chapter').strip())
        chapter_slug = chapter.lower()
        chapter_slug = re.sub(r'\s+', '-', chapter_slug)
        chapter_slug = re.sub(r'[^\w-]', '', chapter_slug)
        chapter_slug = re.sub(r'-{2,}', '-', chapter_slug)

        pubdate = ma.group('pubdate').strip()
        date = '' if pubdate.startswith('0000') else '\ndate: {}'.format(pubdate)

        title = ma.group('title').strip()
        title = remove_crap(title)

        title_slug = title.lower()
        title_slug = re.sub(r'\s+', '-', title_slug)
        title_slug = re.sub(r'[^\w-]', '', title_slug)
        title_slug = re.sub(r'-{2,}', '-', title_slug)

        description = re.sub(r'\s+', ' ', ma.group('description').strip())
        description = remove_crap(description)

        keywords = ma.group('keywords')
        keywords = keywords.lower().strip()

        order = int(ma.group('order'))
        order_slug = f'{order:03}--' if order else ''

        source_mp3 = os.path.join(mp3_dir, ma.group('hi_fi'))
        if not os.path.exists(source_mp3):
          raise ValueError(f'MISSING: {source_mp3}')

        lesson_basename = f'{order_slug}{book_slug}--{chapter_slug}--{title_slug}'
        lesson_mp3 = os.path.join(book_slug, f'{lesson_basename}.mp3')
        lesson_txt = os.path.join(book_slug, f'{lesson_basename}.txt')
        lesson_json = os.path.join(book_slug, f'{lesson_basename}.json')

        rows.append([
          book_slug,
          order,
          chapter_slug,
          title_slug,
          book,
          chapter,
          title,
          description,
          keywords,
          lesson_mp3,
          lesson_txt,
          lesson_json,
        ])

        book_dir = os.path.join(out_dir, book_slug)
        if not os.path.exists(book_dir):
          os.mkdir(book_dir)

        lesson_path = os.path.join(out_dir, lesson_txt)
        with open(lesson_path, 'w') as out:
          kwds = f'\n\nKeywords: {keywords}' if keywords else ''
          print(f'{book} {chapter} - {title}\n\n{description}{kwds}', file=out)

        json_path = os.path.join(out_dir, lesson_json)
        with open(json_path, 'w') as out:
          obj = {
            "book_slug": book_slug,
            "order": order,
            "chapter_slug": chapter_slug,
            "title_slug": title_slug,
            "book": book,
            "chapter": chapter,
            "title": title,
            "description": description,
            "mp3_file": f'{lesson_basename}.mp3',
            "txt_file": f'{lesson_basename}.txt',
          }
          if keywords:
            obj['keywords'] = [kwd.strip() for kwd in keywords.split(',')]

          json.dump(obj, out, sort_keys=True, indent='    ')


        dest_mp3 = os.path.join(out_dir, lesson_mp3)
        if os.path.exists(dest_mp3):
          print(f'{dest_mp3}')
        else:
          print(f'{source_mp3} -> {dest_mp3}')
          shutil.copy(source_mp3, dest_mp3)

      rows.sort(key=lambda r: r[-1])
      out_csv.writerows(rows)


if __name__ == '__main__':
  main(sys.argv[1], sys.argv[2], sys.argv[3])
