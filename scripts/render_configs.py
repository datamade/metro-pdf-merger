if __name__ == "__main__":

    import sys

    from os.path import abspath, dirname, join

    path = abspath(join(dirname(__file__), '..'))
    sys.path.insert(1, path)

    from jinja2 import Template

    deployment_id, deployment_group = sys.argv[1:]

    domains = {
        'staging': 'metro-pdf-merger.datamade.us',
    }

    nginx_template_path = '/home/datamade/metro-pdf-merger-{}/configs/nginx_template.conf'.format(
        deployment_id)
    nginx_outpath = '/etc/nginx/conf.d/metro-pdf-merger.conf'
    supervisor_template_path = '/home/datamade/metro-pdf-merger-{}/configs/supervisor_template.conf'.format(
        deployment_id)
    supervisor_outpath = '/etc/supervisor/conf.d/metro-pdf-merger.conf'

    with open(nginx_template_path) as f:
        nginx_conf = Template(f.read())
        context = {
            'deployment_id': deployment_id,
            'domain': domains[deployment_group]
        }
        nginx_rendered = nginx_conf.render(context)

    with open(supervisor_template_path) as f:
        supervisor_conf = Template(f.read())
        supervisor_rendered = supervisor_conf.render(
            {'deployment_id': deployment_id})

    with open(nginx_outpath, 'w') as out:
        out.write(nginx_rendered)

    with open(supervisor_outpath, 'w') as out:
        out.write(supervisor_rendered)
