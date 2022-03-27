import csv
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

File = open("Experiment 1.txt","r")
text = []

header = ['onetwo', 'twothree', 'onethree']
if True:
    with open('YOUR_CSV_FILE.csv', 'a') as file:
        # creating the csv writer
        file_write = csv.writer(file)
        file_write.writerow(header)

    for line in File:
        text.append(line) if line != "\n" else None
        if len(text) >2:
            first_timer = datetime.strptime(text[0].split("\n")[0], "%Y-%m-%d %H:%M:%S.%f")
            second_timer = datetime.strptime(text[1].split("\n")[0], "%Y-%m-%d %H:%M:%S.%f")
            thrid_timer = datetime.strptime(text[2].split("\n")[0], "%Y-%m-%d %H:%M:%S.%f")
            one_two_three = []
            diff_one_two = (second_timer- first_timer).total_seconds()
            diff_two_three = (thrid_timer-second_timer).total_seconds()
            diff_one_three = (thrid_timer-first_timer).total_seconds()

            one_two_three.append(diff_one_two)
            one_two_three.append(diff_two_three)
            one_two_three.append(diff_one_three)
            with open(r'YOUR_CSV_FILE.csv', 'a') as file:
                # creating the csv writer
                file_write = csv.writer(file)
                file_write.writerow(one_two_three)
            text.clear()



df = pd.read_csv('YOUR_CSV_FILE.csv')



print(df)
df.rename(
    columns={"onetwo":"Time 1-2",
                "twothree":"Time 2-3",
             "onethree":"Time 1-3"}
          ,inplace=True)
print(df.median())
print(df.mean())


box=df.boxplot(column='Time 1-2', showmeans=True)
box.set_ylabel('Seconds')

plt.title("Configuration duration")
plt.savefig("Timer1-2")
plt.clf()
box=df.boxplot(column='Time 2-3', showmeans=True)
box.set_ylabel('Seconds')
plt.title("Duration of server-client communication")
plt.savefig("Timer2-3")
plt.clf()
box=df.boxplot(column='Time 1-3', showmeans=True)
box.set_ylabel('Seconds')
plt.title("Total duration of setup")
plt.savefig("Timer1-3")