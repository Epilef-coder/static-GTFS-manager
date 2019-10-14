import tornado.web
import tornado.ioloop
import time
import json

from utils.logmessage import logmessage
from utils.tables import readTableDB,replaceTableDB

class fareAttributes(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nfareAttributes GET call')
        fareAttributesJson = readTableDB('fare_attributes').to_json(orient='records', force_ascii=False)

        self.write(fareAttributesJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("fareAttributes GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # API/fareAttributes
        start = time.time()
        logmessage('\nfareAttributes POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        # writing back to db
        if replaceTableDB('fare_attributes', data): #replaceTableDB(tablename, data)
            self.write('Saved Fare Attributes data to DB.')
        else:
            self.set_status(400)
            self.write("Error: could not save to DB.")
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("API/fareAttributes POST call took {} seconds.".format(round(end-start,2)))


class fareRules(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nfareRules GET call')
        fareRulesSimpleJson = readTableDB('fare_rules').to_json(orient='records', force_ascii=False)

        self.write(fareRulesSimpleJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("fareRules GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # API/fareRules
        start = time.time()
        logmessage('\nfareRules POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        # writing back to db
        if replaceTableDB('fare_rules', data): #replaceTableDB(tablename, data)
            self.write('Saved Fare Rules data to DB.')
        else:
            self.set_status(400)
            self.write("Error: could not save to DB.")
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("API/fareRules POST call took {} seconds.".format(round(end-start,2)))


class fareRulesPivoted(tornado.web.RequestHandler):
    def get(self):
        start = time.time()
        logmessage('\nfareRulesPivoted GET call')
        fareRulesDf = readTableDB('fare_rules')
        # do pivoting operation only if there is data. Else send a blank array.
        # Solves part of https://github.com/WRI-Cities/static-GTFS-manager/issues/35
        if len(fareRulesDf):
            df = fareRulesDf.drop_duplicates()
            # skipping duplicate entries if any, as pivoting errors out if there are duplicates.
            fareRulesPivotedJson = df.pivot(index='origin_id',\
                columns='destination_id', values='fare_id')\
                .reset_index()\
                .rename(columns={'origin_id':'zone_id'})\
                .to_json(orient='records', force_ascii=False)
        else:
            fareRulesPivotedJson = '[]'

        # multiple pandas ops..
        # .pivot() : pivoting. Keep origin as vertical axis, destination as horizontal axis, and fill the 2D matrix with values from fare_id column.
        # .reset_index() : move the index in as a column so that we can export it to dict further along. from https://stackoverflow.com/a/20461206/4355695
        # .rename() : rename the index column which we've moved in. Proper name is zone_id.
        # .to_dict(orient='records', into=OrderedDict) : convert to flat list of dicts. from https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.to_dict.html

        # to do: if we get a route or two, then order these by the route's sequence.

        self.write(fareRulesPivotedJson)
        # time check, from https://stackoverflow.com/a/24878413/4355695
        end = time.time()
        logmessage("fareRulesPivoted GET call took {} seconds.".format(round(end-start,2)))

    def post(self):
        # API/fareRulesPivoted?pw=${pw}
        start = time.time()
        logmessage('\nfareRulesPivoted POST call')
        pw = self.get_argument('pw',default='')
        if not decrypt(pw):
            self.set_status(400)
            self.write("Error: invalid password.")
            return
        # received text comes as bytestring. Convert to unicode using .decode('UTF-8') from https://stackoverflow.com/a/6273618/4355695
        data = json.loads( self.request.body.decode('UTF-8') )

        # need to unpivot this. We basically need to do the exact same steps as the get(self) function did, in reverse.
        df = pd.DataFrame(data)

        fareRulesArray = pd.melt(df, id_vars=['zone_id'],\
            var_name='destination_id',value_name='fare_id')\
            .rename(columns={'zone_id': 'origin_id'})\
            .replace('', pd.np.nan)\
            .dropna()\
            .sort_values(by=['origin_id','destination_id'])\
            .to_dict('records',into=OrderedDict)

        # pandas: chained many commands together. explaining..
        # .melt(df.. : that's the UNPIVOT command. id_vars: columns to keep. Everthing else "melts" down. var_name: new column name of the remaining cols serialized into one.
        # .rename(.. : renaming the zone_id ('from' station) to origin_id
        # .replace(.. At frontend some cells might have been set to blank. That comes thru as empty strings instead of null/NaN values. This replaces all empty strings with NaN, so they can be dropped subsequently. From https://stackoverflow.com/a/29314880/4355695
        # .dropna() : drop all entries having null/None values. Example ALVA to ALVA has nothing; drop it.
        # sort_values(.. : sort the table by col1 then col2
        # to_dict(.. : output as an OrderedDict.

        # writing back to db
        if replaceTableDB('fare_rules', fareRulesArray):
             self.write('Saved Fare Rules data to DB.')
        else:
            self.set_status(400)
            self.write("Error: could not save to DB.")

        end = time.time()
        logmessage("API/fareAttributes POST call took {} seconds.".format(round(end-start,2)))