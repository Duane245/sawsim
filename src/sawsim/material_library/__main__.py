"""Local material library CLI: list, show, and immutable JSON import."""
import argparse
import json
from pathlib import Path
from . import list_records,get_record,import_record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('list')
    show=sub.add_parser('show');show.add_argument('id');show.add_argument('--version')
    ingest=sub.add_parser('import');ingest.add_argument('file',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='list':
            result=[{k:r[k] for k in ['id','version','name','status','roles']} for r in list_records()]
        elif args.command=='show':result=get_record(args.id,args.version)
        else:result=import_record(json.loads(args.file.read_text(encoding='utf-8')))
    except (ValueError,KeyError,OSError) as exc:parser.error(str(exc))
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))


if __name__=='__main__':main()
