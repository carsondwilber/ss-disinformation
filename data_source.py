import os
import json
import re

from utils.configuration import Configurable
from utils.log import Logging


class DataFilter:
    @staticmethod
    def _validate_condition(c):
        if not isinstance(c, dict):
            raise Exception("Condition must be a dict.")

        terminal = False
        for key in c:
            if key[0] == '$':
                terminal = True
            elif terminal:
                raise Exception(
                    "Terminal options must not be present with other data. '%s' is invalid as a $terminal option is also present." % (key))

        if not terminal:
            for key in c:
                DataFilter._validate_condition(c[key])
            return

        for key in c:
            if not key in ["$eq", "$lt", "$gt", "$lte", "$gte", "$regex"]:
                raise Exception(
                    "Terminal option must be one of ['$eq', '$lt', '$gt', '$lte', '$gte', '$regex']. '%s' is not a valid terminal option." % (key))

        nc = any([k in c for k in ["$lt", "$gt", "$lte", "$gte"]])
        if nc:
            if "$eq" in c:
                raise Exception(
                    "Cannot specify a numerical comparative operator ($lt, $gt, $lte, $gte) with $eq as it is redundant or invalid.")

        if (nc or "$eq" in c) and "$regex" in c:
            raise Exception(
                "Cannot specify a numerical operator ($eq, $lt, $gt, $lte, $gte) with $regex as they imply conflicting types (string and number).")

        if "$lt" in c and "$lte" in c:
            raise Exception(
                "Cannot specify $lte along with $lt (only one allowed.)")

        if "$gt" in c and "gte" in c:
            raise Exception(
                "Cannot specify $gte along with $gt (only one allowed.)")

        for key in c:
            if key in ["eq", "$lt", "$gt", "$lte", "$gte"]:
                if not isinstance(c[key], (int, float)):
                    raise Exception(
                        "Cannot specify a non-numerical value for numerical operators $eq, $lt, $gt, $lte, $gte. '%s' is not a numerical value." % (c[key]))

        if "$lt" in c:
            if "$gt" in c:
                if c["$lt"] <= c["$gt"]:
                    raise Exception(
                        "Cannot specify $lt with $gt if ranges do not overlap. Ranges: (-inf, %d) U (%d, inf)." % (c["$lt"], c["$gt"]))
            elif "$gte" in c:
                if c["$lt"] <= c["$gte"]:
                    raise Exception(
                        "Cannot specify $lt with $gte if ranges do not overlap. Ranges: (-inf, %d) n [%d, inf)." % (c["$lt"], c["$gte"]))
        elif "$lte" in c:
            if "$gt" in c:
                if c["$lte"] <= c["$gt"]:
                    raise Exception(
                        "Cannot specify $lte with $gt if ranges do not overlap. Ranges: (-inf, %d] U (%d, inf)." % (c["$lte"], c["$gt"]))
            elif "$gte" in c:
                if c["$lte"] < c["$gte"]:
                    raise Exception(
                        "Cannot specify $lte with $gte if ranges do not overlap. Ranges: (-inf, %d] n [%d, inf)." % (c["$lte"], c["$gte"]))
                elif c["$lte"] == c["$gte"]:
                    raise Exception(
                        "Cannot specify $lte with $gte if ranges overlap at a single value; use $eq instead. Ranges: (-inf, %d] n [%d, inf)." % (c["$lte"], c["$gte"]))

    @staticmethod
    def _validate_operator(o):
        if not isinstance(o, list):
            raise Exception("Operator value must be a list.")

        if not len(o) > 0:
            raise Exception(
                "Operator value must have at least 1 suboperator or condition.")

        for i, co in enumerate(o):
            if not isinstance(co, dict):
                raise Exception(
                    "Operator value number %d must be a dict." % (i))

            if "$and" in o or "$or" in o:
                if not len(o) == 1:
                    raise Exception(
                        "An operator must only contain one of ['$and', '$or'].")

                # Will only execute once as there is only one key
                for key in o:
                    DataFilter._validate_operator(co[key])
            else:
                try:
                    DataFilter._validate_condition(co)
                except Exception as e:
                    raise Exception(
                        "Failed to validate condition number %d: %s" % (i + 1, e))

    @staticmethod
    def validate_filter(f):
        try:
            if not isinstance(f, dict):
                raise Exception("Top-level type must be a dict.")

            if not len(f) > 0:
                raise Exception(
                    "Top-level dict must only contain one condition.")

            for key in f:
                if not key in ["$and", "$or"]:
                    raise Exception(
                        "Top-level dict must contain one of ['$and', '$or'] as its only key.")

                DataFilter._validate_operator(f[key])
        except Exception as e:
            raise Exception("Failed to validate filter: %s" % (e)) from None

    @staticmethod
    def _match_condition(c, d):
        terminal = False
        for key in c:
            if key[0] == '$':
                terminal = True
                break

        if not terminal:
            matched = True
            for key in c:
                if key in d:
                    matched &= DataFilter._match_condition(c[key], d[key])
                else:
                    return False
            return matched

        if "$eq" in c:  # "$regex" in c:
            return d == c["$eq"]
        elif "$regex" in c:
            if not isinstance(d, str):
                raise Exception(
                    "Data contains a non-string value being matched against a RegEx pattern: '%s'" % (str(d)))

            pattern = re.compile(c["$regex"])

            return pattern.match(d) != None
        else:  # any([k in c for k in ["$lt", "$gt", "$lte", "$gte"]]):
            if not isinstance(d, (int, float)):
                raise Exception(
                    "Data contains a non-numerical value being matched against numerical operators: '%s'" % (str(d)))

            matched = True

            if "$lt" in c:
                matched &= d < c["$lt"]
            elif "$lte" in c:
                matched &= d <= c["$lte"]

            if "$gt" in c:
                matched &= d > c["$gt"]
            elif "$gte" in c:
                matched &= d >= c["$gte"]

            return matched

    @staticmethod
    def parse(string):
        f = None

        try:
            if not isinstance(string, str):
                raise Exception("Data filter input must be a string.")

            if not len(string) > 1:
                raise Exception(
                    "Data filter input string must be at least 2 characters long.")

            try:
                f = json.loads(string)
            except:
                raise Exception(
                    "Data filter input string must be a valid JSON object.")

            DataFilter.validate_filter(f)
        except Exception as e:
            raise Exception("Failed to parse filter: %s" % (e)) from None

        return f

    def __init__(self, json: dict = None, string: str = None):
        if string is not None and json is not None:
            raise Exception("May only pass a string or JSON object, not both.")
        elif string is None and json is None:
            raise Exception("Must pass a string or JSON object.")

        if string is not None:
            if not isinstance(string, str):
                raise Exception("Filter string must be a string.")
            self.filter = DataFilter.parse(string)
        elif json is not None:
            DataFilter.validate_filter(json)
            self.filter = json

    # TODO: implement dynamic creation of filters

    def _apply(self, o, c, item):
        if o == '$and':
            matched = True
            for i in c:
                if "$and" in i:
                    matched &= self._apply("$and", i["$and"], item)
                elif "$or" in i:
                    matched &= self._apply("$or", i["$or"], item)
                else:
                    matched &= DataFilter._match_condition(i, item)
            return matched
        elif o == "$or":
            for i in c:
                if "$and" in i:
                    if self._apply("$and", i["$and"], item):
                        return True
                elif "$or" in i:
                    if self._apply("$or", i["$or"], item):
                        return True
                elif DataFilter._match_condition(i, item):
                    return True
        else:
            raise Exception(
                "Unknown operator '%s'. How did this get here?" % (o))

    def apply(self, data):
        items = []
        for item in data["references"]:
            for key in self.filter:
                if self._apply(key, self.filter[key], item):
                    items.append(item)
        return items


class DataSieve:
    @staticmethod
    def validate_sieve(s):
        try:
            if not isinstance(s, dict):
                raise Exception("Top-level type must be a dict.")

            if not len(s) > 0:
                raise Exception(
                    "Top-level dict must only contain one platform.")

            for key in s:
                if not isinstance(s[key], (str, list)):
                    raise Exception(
                        "Each platform must only a list of account labels or a string of an account label.")

                if isinstance(s[key], list):
                    for label in s[key]:
                        if not isinstance(label, str):
                            raise Exception(
                                "Each account label must be a string.")
        except Exception as e:
            raise Exception("Failed to validate filter: %s" % (e)) from None

    @staticmethod
    def parse(string: str):
        s = None

        try:
            if not isinstance(string, str):
                raise Exception("Data sieve input must be a string.")

            if not len(string) > 1:
                raise Exception(
                    "Data sieve input string must be at least 2 characters long.")

            try:
                s = json.loads(string)
            except:
                raise Exception(
                    "Data sieve input string must be a valid JSON object.")

            DataSieve.validate_sieve(s)
        except Exception as e:
            raise Exception("Failed to parse sieve: %s" % (e)) from None

        return s

    def __init__(self, string: str = None, json: str = None):
        if string is not None and json is not None:
            raise Exception("May only pass a string or JSON object, not both.")
        elif string is None and json is None:
            raise Exception("Must pass a string or JSON object.")

        if string is not None:
            if not isinstance(string, str):
                raise Exception("Sieve string must be a string.")
            self.sieve = DataSieve.parse(string)
        elif json is not None:
            DataSieve.validate_sieve(json)
            self.sieve = json

    def apply(self, data):
        result = []
        for item in data:
            user = item.copy()

            # Remove extra platform data from item
            for platform in user["platforms"]:
                if not platform in self.sieve.keys():
                    del user["platforms"][platform]

            for platform in user["platforms"]:
                labels = [self.sieve[platform]]
                if isinstance(self.sieve[platform], list):
                    labels = self.sieve[platform]
                for label in [label for label in user["platforms"][platform]]:
                    if label not in labels:
                        del user["platforms"][platform][label]
                        if len(user["platforms"][platform]) == 0:
                            del user["platforms"][platform]

            if len(user["platforms"]) > 0:
                result.append(user)

        return result


class DataSource(Logging, Configurable):
    @staticmethod
    def validate_data(data):
        for key in data:
            if not key in ["name", "version", "references"]:
                raise Exception(
                    "Unknown key in data: '%s'. Keys must be one of ['name', 'version', 'references']." % (key))

            if not "name" in data:
                raise Exception("Source list must contain a 'name'.")

            if not "version" in data:
                raise Exception("Source list must contain a 'version'.")

            if not "references" in data:
                raise Exception("Source list must contain 'references'.")

            name = data["name"]

            if not isinstance(name, str):
                raise Exception("Source list name must be a string.")

            if not len(name) > 0:
                raise Exception(
                    "Source list name must be at least 1 character long.")

            version = data["version"]

            if not isinstance(version, int):
                raise Exception("Source list version must be an integer.")

            if not version > 0:
                raise Exception("Source list version must be positive.")

            references = data["references"]

            if not isinstance(references, list):
                raise Exception("Source list references must be a list.")

            for i, item in enumerate(references):
                if not isinstance(item, dict):
                    raise Exception(
                        "Source list reference number %d must be a dict." % (i + 1))

    def __init__(self, source: str):
        try:
            if not os.path.exists(source):
                raise Exception("Source path does not exist.")

            with open(source, 'r', encoding='utf-8') as f:
                raw = f.read()

            data = json.loads(raw)

            DataSource.validate_data(data)

            self.data = data
        except Exception as e:
            raise Exception(
                "Failed to load data from source '%s': %s" % ()) from None

    def filter(self, f: DataFilter):
        if not isinstance(f, DataFilter):
            raise Exception(
                "Must pass an instance of DataFilter to perform filtering.")

        return f.apply(self.data)
