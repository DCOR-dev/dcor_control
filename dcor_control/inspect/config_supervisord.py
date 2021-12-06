from .common import ask
from .paths import get_supervisord_worker_path


def check_supervisord(autocorrect):
    """Check whether the separate dcor worker files exist"""
    svd_path = get_supervisord_worker_path()
    for worker in ["long", "normal", "short"]:
        wpath = svd_path.with_name("ckan-worker-dcor-{}.conf".format(worker))
        if not wpath.exists():
            if autocorrect:
                wcr = True
                print("Creating '{}'.".format(wpath))
            else:
                wcr = ask("Supervisord entry 'dcor-{}' missing".format(worker))
            if wcr:
                data = svd_path.read_text()
                data = data.replace(
                    "[program:ckan-worker]",
                    "[program:ckan-ckan-worker-dcor-{}]".format(worker))
                data = data.replace(
                    "/ckan.ini jobs worker",
                    "/ckan.ini jobs worker dcor-{}".format(worker))
                wpath.write_text(data)
