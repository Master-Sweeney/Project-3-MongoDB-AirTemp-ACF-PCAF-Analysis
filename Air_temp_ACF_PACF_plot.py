#Import neccessary libraries
from pprint import PrettyPrinter 
from pymongo import MongoClient
from urllib.parse import quote_plus
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from pymongo.server_api import ServerApi

#Verify successful connection to MongoDB dataset
uri = "mongodb+srv://<username>:<password>@cluster0.nmsil9a.mongodb.net/?appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
#Connect to server with personal client details
client = MongoClient("mongodb+srv://<username>r:<password>@cluster0.nmsil9a.mongodb.net/?appName=Cluster0")

#Get list of database names
db_names = client.list_database_names()
print("Database Names:")
for name in db_names:
    print(f"* {name}")
    
#Extract 'sample_weatherdata' for exploration of autocorrelation function and data distribution
pp = PrettyPrinter(indent=4) #Make outputs readable/ more presentable
db = client['sample_weatherdata']

#Retrieve list of collections available in sample_weatherdata database and get count of documents available
collection_list = db.list_collection_names()

for c in collection_list:
    pp.pprint(c)

weather_data = db['data']
weather_data.count_documents({})

#Determine how many types of weather observation readings are available in collection
weather_data.distinct('type')

#Observe document examples
result = weather_data.find_one({})
pp.pprint(result)

#Count the number of observations for the weather type we are interested in 
print("Documents of type FM-13:", weather_data.count_documents({"type":"FM-13"}))

#Create a query to present the number of documents for each type
result = weather_data.aggregate(
    [
        {"$group":{"_id":"$type","count":{"$count":{}}}}
    
    ]
)
pp.pprint(list(result))

#Create query to extract airtemperatur and timestamp data for AutoCorrelation function analysis
final_result = weather_data.find(
    {"type":"FM-13"},
    projection = {"airTemperature":1, "ts":1, "_id":0}
)
pp.pprint(final_result.next())

#Transform query into dataframe
df = pd.DataFrame(final_result).set_index("ts")

#Convert airTemperature readings into seperate labels to differentiate between 'value' and 'quality'
value_ls = []
quality_ls = []
for record in range(len(df["airTemperature"])):
    value = df["airTemperature"][record]['value']
    quality = df["airTemperature"][record]['quality']
    value_ls.append(value)
    quality_ls.append(quality)

df["value"] = pd.Series(value_ls).values
df["quality"] = pd.Series(quality_ls).values

#Drop airTemperature column as it is no longer necessary for our exploration
df.drop(columns = "airTemperature", inplace = True)

#Use forward fill method to take replace all null values within the readings, and turn it into a dataframe
df["value"].resample("1H").mean().fillna(method = "ffill").to_frame()

#Plot rolling average of temperature value readings over a weekly period
fig, ax = plt.subplots(figsize=(15,6))
df["value"].rolling(16).mean().plot(ax=ax,
                                     ylabel="Temp value",
                                     xlabel="Time",
                                     title="Weekly Rolling Average");

#Shift value readings by 1 time frame (1 hour) to allow for autocorrelation analysis
df["value.L1"] = df["value"].shift(1)
df.dropna(inplace = True)

#Plot Autocorrelation function and Partial autocorrelation function plot
fig, ax = plt.subplots(figsize = (16,6))
acf_values = df["value"].resample("1H").mean().fillna(method = "ffill")
plot_acf(acf_values,ax=ax);

fig, ax = plt.subplots(figsize = (16,6))
pacf_values = df["value"].resample("1H").mean().fillna(method = "ffill")
plot_pacf(pacf_values,ax=ax);
