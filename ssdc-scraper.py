import sys
import argparse
import csv

from tweepy_utils import TwitterHarvester
from utils.credentials import CredentialManager
from data_source import DataSource, DataFilter, DataSieve

valid_options = {
    "actions": {
        "timeline": {
            "limit": int
        }
    }
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Scrape data for the SSDC project.")  # noqa
    parser.add_argument("--source", type=str, required=True, help="Load this source file.")  # noqa
    parser.add_argument("--select", type=str, required=True, help="Select this reference point for each source item.")  # noqa
    parser.add_argument("--action", choices=["timeline"], required=True, help="Perform this action on the given sources.")  # noqa
    parser.add_argument("--filter", type=str, help="Filter options to apply to source files.")  # noqa
    parser.add_argument("--credentials", type=str, default="./credentials.ini", help="Credential configuration file to use.")  # noqa
    parser.add_argument("--credential-name", type=str, default="twitter-ssdc-consumer", help="Credential configuration file to use.")  # noqa
    parser.add_argument("--option", type=str, action='append', help="Additional options to apply while performing action.")  # noqa
    parser.add_argument("--output", type=str, help="Output result to a single file. (Coming Soon: output different files for each source, entity, etc.)")  # noqa
    args = parser.parse_args(sys.argv[1:])

    options = {}
    if args.option is not None:
        for option in args.option:
            name = option
            value = True
            valid = False

            if '=' in option:
                name, value = option.split('=')

            if '*' in valid_options:
                if name in valid_options:
                    valid = True
            if not valid and 'actions' in valid_options:
                if args.action in valid_options['actions']:
                    if name in valid_options['actions'][args.action]:
                        valid = True
                        value = valid_options['actions'][args.action][name](
                            value)

    if not len(args.source) > 0:
        raise Exception("Must specify at least one data source list.")

    manager = CredentialManager()
    manager.load_credentials(path=args.credentials)

    harvester = TwitterHarvester()
    harvester.init(manager.credentials[args.credential_name])

    source = DataSource(args.source)
    users = source.data["references"]

    if args.filter:
        dfilter = DataFilter(string=args.filter)
        users = dfilter.apply(source.data)

    dsieve = DataSieve(string=args.select)
    users = dsieve.apply(users)

    result = None

    for user in users:
        for platform in user["platforms"]:
            if platform == "Twitter":
                for label in user["platforms"]["Twitter"]:
                    if args.action == 'timeline':
                        if 'limit' in options:
                            result = harvester.collect_user_timeline(
                                user["platforms"]["Twitter"][label], limit=options['limit'])
                        else:
                            result = harvester.collect_user_timeline(
                                user["platforms"]["Twitter"][label])

    if result is not None and args.output is not None:
        with open(args.output, 'w', encoding='utf-8') as f:
            w = csv.writer(f)

            w.writerow(['timestamp', 'tweet_text', 'username',
                        'all_hashtags', 'followers_count', 'location'])

            for tweet in result:
                w.writerow([tweet.created_at, tweet.full_text.replace('\n', ' ').encode('utf-8'), tweet.user.screen_name.encode('utf-8'),
                            [e['text'] for e in tweet._json['entities']['hashtags']], tweet.user.followers_count, tweet.user.location.encode('utf-8')])
