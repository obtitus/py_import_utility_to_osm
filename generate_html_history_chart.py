import os
import csv
import logging
logger = logging.getLogger('barnehagefakta.generate_html.history_chart')

import codecs
def open_utf8(filename, *args, **kwargs):
    logger.debug('open(%s, %s, %s)', filename, args, kwargs)
    return codecs.open(filename, *args, encoding="utf-8-sig", **kwargs)
from jinja2 import Template

def get_history_data(history_filename):
    with open(history_filename, 'r') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for row in reader:
            row[0] = float(row[0])
            row[1] = int(row[1]) - int(row[2])
            row[2] = int(row[2])

            row[1], row[2] = row[2], row[1]
            yield row

def render_history_chart(root, header=['Antall barnehager med no-barnehage:nsrid i OSM', ''],
                         title='Totalt antall barnehager og antall importerte',
                         chart_id='id_history'):
    history_filename = os.path.join(root, 'history.csv')
    chart_template = os.path.join(root, 'templates', 'draw_chart_template.js')
    
    with open_utf8(chart_template) as f:
        chart_template = Template(f.read())

    data = list(get_history_data(history_filename))
    
    chart = chart_template.render(data=data,
                                  title=title,
                                  chart_id=chart_id,
                                  header=header)
    return chart
            
def main(root):
    index_output = os.path.join(root, 'index.html')
    index_template = os.path.join(root, 'templates', 'index_template.html')
    
    with open_utf8(index_template) as f:
        index_template = Template(f.read())

    chart = render_history_chart(root)

    page = index_template.render(chart=chart, now=1)
    
    with open_utf8(index_output, 'w') as output:
        output.write(page)

if __name__ == '__main__':
    from utility_to_osm import argparse_util
    parser = argparse_util.get_parser('Generate the html history chart')
    parser.add_argument('--root', default='.',
                        help="Specify the input/output directory, defaults to current directory")        
    argparse_util.add_verbosity(parser, default=logging.WARNING)

    args = parser.parse_args()
    
    logging.basicConfig(level=args.loglevel)

    main(root=args.root)
    
