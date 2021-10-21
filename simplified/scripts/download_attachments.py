'''
Download specified attachments into the attachments/ directory and return
space-delimited list of attachment filenames.

Can use scrapelib for retrying requests.

TBD: How to pass data from compile_pdfs management command to this container.
Some options: https://www.astronomer.io/guides/airflow-passing-data-between-tasks
'''
import sys

sys.stdout.write('attachments/foo.xlsx attachments/bar.doc attachments/baz.pdf')