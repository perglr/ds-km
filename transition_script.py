import json
import os


class UIDTable:

    def __init__(self):
        self.table = {}

    def add_chapter(self, chapter_data):
        table = {}
        for q in chapter_data['questions']:
            table[q['questionid']] = {'uid': q['uid'], 'answers': {}}
            for a in q.get('answers', []):
                table[q['questionid']]['answers'][a['id']] = a['uid']
        self.table[chapter_data['chapterid']] = table

    def lookup_uid(self, chid, qid, aid=None):
        if aid is None:
            return self.table[chid][qid]['uid']
        return self.table[chid][qid]['answers'][aid]


def rewrite_references(table, filepath):
    with open(filepath) as f:
        data = json.load(f)
    chid = data['chapterid']
    for q in data['questions']:
        if 'precondition' in q:
            p = q['precondition']
            q['precondition']['uid'] = table.lookup_uid(
                chid, p['questionid'], p.get('answerid', None)
            )
        for r in q.get('references', []):
            if r['type'] != 'xref':
                continue
            r['uid'] = table.lookup_uid(
                r['chapterid'], r['questionid'], r.get('answerid', None)
            )
            del r['chapterid']
            del r['questionid']
            if 'answerid' in r:
                del r['answerid']
        del q['questionid']
        for a in q.get('answers', []):
            del a['id']
    with open(filepath, mode='w') as f:
        json.dump(data, f, sort_keys=False,
                  indent=4, separators=(',', ': '))


def iter_files(root):
    for act_dir, dirs, files in os.walk(root):
        for name in files:
            if name.startswith('chapter') and name.endswith('.json'):
                yield os.path.join(act_dir, name)

def run(root='./datamodel/core'):
    table = UIDTable()
    for filepath in iter_files(root):
        with open(filepath) as f:
            data = json.load(f)
            table.add_chapter(data)
    for filepath in iter_files(root):
        rewrite_references(table, filepath)

if __name__ == '__main__':
    run()
