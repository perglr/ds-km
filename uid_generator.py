import click
import json
import os
import random
import sys
from collections import OrderedDict


ALPHABET = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
LENGTH = 5
MAX_TRIES = 1000


def warn(msg):
    print('Warning: ' + msg, file=sys.stderr)


def generate_string(length, alphabet):
    return ''.join(
        [random.choice(alphabet) for _ in range(length)]
    )


def generate_unique_string(existing):
    new_uid = generate_string(LENGTH, ALPHABET)
    i = 0
    while new_uid in existing:
        new_uid = generate_string(LENGTH, ALPHABET)
        i += 1
        if i > MAX_TRIES:
            raise RuntimeError(
                'Generated ID not unique within {} tries'.format(MAX_TRIES)
            )
    return new_uid


def iter_datamodel_chapter(root):
    for act_dir, dirs, files in os.walk(root):
        for name in files:
            if name.startswith('chapter') and name.endswith('.json'):
                with open(os.path.join(act_dir, name)) as f:
                    yield json.load(f)


def walk_datamodel_uids(root):
    quids = set()
    for chapter in iter_datamodel_chapter(root):
        question_n = 0
        for question in chapter['questions']:
            question_n += 1
            if 'uid' not in question:
                    warn('UID not set in {}:{}:{}'.format(
                        chapter['namespace'],
                        chapter['chapterid'],
                        question_n
                    ))
            elif question['uid'] in quids:
                warn('UID not unique in {}:{}:{}'.format(
                    chapter['namespace'],
                    chapter['chapterid'],
                    question_n
                ))
            else:
                quids.add(question['uid'])
            answer_n = 0
            for answer in question.get('answers', []):
                    if 'uid' not in answer:
                        warn('UID not set in {}:{}:{}:{}'.format(
                            chapter['namespace'],
                            chapter['chapterid'],
                            question_n,
                            answer_n
                        ))
                    elif answer['uid'] in quids:
                        warn('UID not unique in {}:{}:{}:{}'.format(
                            chapter['namespace'],
                            chapter['chapterid'],
                            question_n,
                            answer_n
                        ))
                    else:
                        quids.add(answer['uid'])
    return quids


def create_missing_uids(uids, chapter):
    for question in chapter['questions']:
        if 'uid' not in question:
            question['uid'] = generate_unique_string(uids)
            uids.add(question['uid'])
        question.move_to_end('uid', last=False)
        for answer in question.get('answers', []):
            if 'uid' not in answer:
                answer['uid'] = generate_unique_string(uids)
                uids.add(answer['uid'])
            answer.move_to_end('uid', last=False)
    return chapter

@click.group()
@click.argument('dskm-root', type=click.Path())
@click.version_option(version='0.1', prog_name='DS KM UID generator')
@click.pass_context
def cli(ctx, dskm_root):
    ctx.obj['root'] = dskm_root


@cli.command()
@click.option('-n', '--count', default=1, type=int)
@click.pass_context
def generate_uid(ctx, count):
    root = ctx.obj['root']
    uids = walk_datamodel_uids(root)
    for i in range(count):
        x = generate_unique_string(uids)
        uids.add(x)
        print(x)


@cli.command()
@click.pass_context
def create_uids(ctx):
    root = ctx.obj['root']
    uids = set()
    for act_dir, dirs, files in os.walk(root):
        for name in files:
            if name.startswith('chapter') and name.endswith('.json'):
                filepath = os.path.join(act_dir, name)
                with open(filepath, 'r') as f:
                    data = json.load(f, object_pairs_hook=OrderedDict)
                data = create_missing_uids(uids, data)
                with open(filepath, 'w') as f:
                    json.dump(data, f, sort_keys=False,
                              indent=4, separators=(',', ': '))


if __name__ == '__main__':
    cli(obj={})
