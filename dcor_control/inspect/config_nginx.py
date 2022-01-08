from dcor_shared.paths import get_nginx_config_path

from .common import ask


def check_nginx(cmbs, autocorrect=False):
    path_nginx = get_nginx_config_path()
    with open(path_nginx) as fd:
        lines = fd.readlines()
    for ii, line in enumerate(lines):
        if not line.strip() or line.startswith("#"):
            continue
        elif line.strip().startswith("client_max_body_size"):
            cur = line.strip().split()[1].strip(";")
            if cur != cmbs:
                if autocorrect:
                    print("Setting client_max_body_size to {}".format(cmbs))
                    correct = True
                else:
                    correct = ask("'client_max_body_size' should be "
                                  + "'{}', but is '{}'".format(cmbs, cur))
                if correct:
                    lines[ii] = line.replace(cur, cmbs)
                    path_nginx.write_text("\n".join(lines))
            break
    else:
        raise ValueError("'client_max_body_size' not set!")
