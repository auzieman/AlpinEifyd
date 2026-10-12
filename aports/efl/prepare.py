"""Carry the three source fixes proven by the earlier EFL build."""
from pathlib import Path

p = Path('meson.build')
old = "['exactness'        ,[]                    , false,  false,  true,"
text = p.read_text()
if old not in text:
    raise SystemExit('EFL source changed: expected exactness setting absent')
p.write_text(text.replace(old, old.replace('true,', 'false,'), 1))
p = Path('src/bin/elementary/test_win_stack.c')
text = p.read_text()
p.write_text(text.replace('\n_del()\n', '\n_del(void *data EINA_UNUSED, Evas *e EINA_UNUSED, Evas_Object *obj EINA_UNUSED, void *event_info EINA_UNUSED)\n'))
for p in Path('src/bin/embryo').glob('embryo_cc_sc*.[ch]'):
    p.write_text(p.read_text().replace('constexpr', 'embryo_constexpr'))
