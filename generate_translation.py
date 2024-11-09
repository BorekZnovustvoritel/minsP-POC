import os
from pathlib import Path

from jinja2 import Environment, PackageLoader
from jinja2.nodes import Getattr, Name

from definitions import TRANSLATION_DIR, TEMPLATES_DIR


def get_jinja_words(file: str | Path) -> set[str]:
    if isinstance(file, Path):
        file = file.name
    env = Environment(
        loader=PackageLoader("generate_translation", str(TEMPLATES_DIR.absolute()))
    )
    template_source = env.loader.get_source(env, file)
    parsed_content = env.parse(template_source)
    nodes = filter(
        lambda x: isinstance(x.node, Name) and x.node.name == "translation",
        parsed_content.find_all(Getattr),
    )
    keywords = {node.attr for node in nodes}

    return keywords


def get_po_words(file: Path) -> dict[str, str]:
    if not file.exists():
        return {}
    with open(file, "r") as inp_file:
        lines = inp_file.readlines()
    ans = {}
    last_key = None

    reading_id = True
    for line in lines:
        if not line:
            continue
        if line.startswith("msgid"):
            reading_id = True
            last_key = line.replace("msgid ", "").strip().strip('"')
        elif line.startswith("msgstr"):
            reading_id = False
            ans[last_key] = line.replace("msgstr ", "").strip().strip('"')
        else:
            stripped_line = line.strip().strip('"')
            if reading_id:
                last_key += stripped_line
            else:
                ans[last_key] += stripped_line
    ans = {key: value for key, value in ans.items() if key}
    return ans


def merge_words(po_words: dict[str, str], additional_words: set[str]) -> dict[str, str]:
    ans = dict(po_words)
    for word in additional_words:
        ans[word] = ""
    return ans


def write_po(words_dict: dict[str, str], file: Path):
    with open(file, "w") as out_file:
        out_file.write('msgid ""\n')
        out_file.write('msgstr ""\n')
        out_file.write(r'"Content-Type: text/plain; charset=UTF-8\n"' + "\n")
        for key in sorted(words_dict.keys()):
            out_file.write("\n")
            msgid_lines = [line for line in key.split(r"\n")]
            while msgid_lines and not msgid_lines[-1]:
                msgid_lines = msgid_lines[:-1]
            msgid = '\\n"\n"'.join(msgid_lines)
            msgstr_lines = [line for line in words_dict[key].split(r"\n")]
            while msgstr_lines and not msgstr_lines[-1]:
                msgstr_lines = msgstr_lines[:-1]
            msgstr = '\\n"\n"'.join(msgstr_lines)
            out_file.write(f'msgid "{msgid}"\n')
            out_file.write(f'msgstr "{msgstr}"\n')


if __name__ == "__main__":
    all_words = set()
    dictionaries = {}
    for lang in TRANSLATION_DIR.iterdir():
        po_file = lang / "LC_MESSAGES" / "app.po"
        if not po_file.exists():
            os.makedirs(po_file.parent, exist_ok=True)
        words = get_po_words(po_file)
        all_words.update(words.keys())
        dictionaries[lang.name] = words
    for template in TEMPLATES_DIR.iterdir():
        all_words.update(get_jinja_words(template))
    for lang, word_dict in dictionaries.items():
        new_dict = {key: "" for key in all_words}
        new_dict.update(word_dict)
        print(list(all_words))
        write_po(new_dict, TRANSLATION_DIR / lang / "LC_MESSAGES" / "app.po")
