from parse import *
import matplotlib.pyplot as plt
import numpy as np
from wordcloud import WordCloud
from matplotlib.dates import date2num, num2date
from matplotlib import dates as dt
import seaborn as sns
import sys
import pytz
import subprocess
from io import BytesIO
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader

DIR = [os.getcwd() + "/messages/inbox/",os.getcwd() + "/messages/filtered_threads/",os.getcwd() +  "/messages/archived_threads/"]
DIR = [Msgdirect for Msgdirect in DIR if os.path.isdir(Msgdirect)]
assert DIR, "No messges directory found"
new_image_dir = os.getcwd() + "/Images/"

class Analysis:
    def __init__(self):
        self.heatmapHeight = 0
        self.wordHeight = 0
        self.pageWidth = 1800
        self.basePageHeight = 1500
        self.figureWidthInches = 18
        self.figureHeightInches = self.figureWidthInches / 3

        self.figureWidthPix = self.figureWidthInches * 100
        self.figureHeightPix = self.figureHeightInches * 100

    def getConversations(self):
        conversation_files=[]
        for Msgdirect in DIR:
            conversation_files.append(os.listdir(Msgdirect))
            conversation_files[-1].sort()
        assert conversation_files, "No conversation found"
        return conversation_files

    def createScatterChart(self):
        print("Creating line chart")
        dates = self.p.get_line_chart_data()
        fig, ax = plt.subplots(1, 1, figsize=(self.figureWidthInches, self.figureHeightInches))

        for user in dates:
            y = list(dates[user].values())
            x = [date2num(date) for date in list(dates[user].keys())]
            plt.scatter(x, y, label=user, s=10)
            ax.xaxis.set_major_formatter(dt.DateFormatter('%b %d, %Y'))

        plt.gca().spines["top"].set_alpha(.3)
        plt.gca().spines["bottom"].set_alpha(.3)
        plt.gca().spines["right"].set_alpha(.3)
        plt.gca().spines["left"].set_alpha(.3)

        ax.set_xlabel('Date', fontsize=20)
        ax.set_ylabel('Number of messages', fontsize=20)
        ax.grid(alpha=.4)

        plt.title("All messages sent in conversation history", fontsize=30)
        plt.legend()
        plt.savefig(new_image_dir + 'line_history.png', dpi=400)
        plt.clf()
        #plt.show()

    def createHeatmap(self):
        print("Creating heatmap")
        hour_index = [h for h in range(23)]
        day_index = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        days = self.p.get_heatmap_data()
        fig = plt.figure(figsize=(self.figureWidthInches, self.figureHeightInches * len(days)))
        for i, user in enumerate(days):
            ax = fig.add_subplot(len(days), 1, i + 1)
            sns.heatmap(days[user], cmap='Blues', linewidths=2, yticklabels=day_index)
            ax.set_title("Hourly heatmap of messages sent by " + user, fontsize=30)
            self.heatmapHeight += self.figureHeightPix
        plt.tight_layout()
        plt.savefig(new_image_dir + 'hourly_heatmap.png', dpi=400)
        plt.clf()

    def createWordcloud(self):
        print("Creating wordcloud")
        messages = self.p.get_all_messages_for_wordcloud()
        fig = plt.figure(figsize=(self.figureWidthInches, self.figureHeightInches * len(messages)))
        for i, user in enumerate(messages):
            ax = fig.add_subplot(len(messages), 1, i + 1)
            wc = WordCloud(background_color='white', width=self.pageWidth, height=int(self.pageWidth/3)).generate(messages[user])
            plt.imshow(wc, interpolation='bilinear')
            plt.title("Wordcloud of messages sent by " + user, fontsize=30)
            self.wordHeight += self.figureHeightPix
        plt.tight_layout()
        plt.savefig(new_image_dir + 'wordcloud.png', dpi=400)
        plt.clf()

    def createPieChart(self):
        print("Creating pie chart")
        fig = plt.figure(figsize=(self.figureWidthInches, self.figureHeightInches))

        num_messages_data = self.p.get_num_messages_of_all_users()
        users = list(num_messages_data.keys())
        num_messages = list(num_messages_data.values())

        num_words_data = self.p.get_num_words_of_all_users()
        num_words = list(num_words_data.values())

        starter_data = self.p.get_data_for_conversation_starter()
        num_starters = list(starter_data.values())

        def func(pct, allvals):
            absolute = int(pct / 100. * np.sum(allvals))
            return "{:.1f}%\n({:d})".format(pct, absolute)

        ax = fig.add_subplot(141)
        pie = ax.pie(num_messages, autopct=lambda pct: func(pct, num_messages), textprops=dict(color="w"))
        ax.set_title("Messages sent", fontsize=30)

        ax = fig.add_subplot(142)
        pie = ax.pie(num_words, autopct=lambda pct: func(pct, num_words), textprops=dict(color="w"))
        ax.set_title("Words sent", fontsize=30)

        ax = fig.add_subplot(143)
        pie = ax.pie(num_starters, autopct=lambda pct: func(pct, num_starters), textprops=dict(color="w"))
        ax.set_title("Conversations started", fontsize=30)

        ax = fig.add_subplot(144)
        ax.axis("off")
        ax.legend(pie[0], users, loc="center")

        plt.tight_layout()
        plt.savefig(new_image_dir + 'pie.png', dpi=400)
        plt.clf()

    def createSentimentAnalysis(self):
        print("Creating sentiment chart")
        sentiment = self.p.get_data_for_sentiment_chart()
        fig, ax = plt.subplots(1, 1, figsize=(16, 9), dpi=72)

        for user in sentiment:
            y = list(sentiment[user].values())
            x = [date2num(date) for date in list(sentiment[user].keys())]
            plt.scatter(x, y, label=user, s=10)
            ax.xaxis.set_major_formatter(dt.DateFormatter('%b %d, %Y'))

        plt.gca().spines["top"].set_alpha(.3)
        plt.gca().spines["bottom"].set_alpha(.3)
        plt.gca().spines["right"].set_alpha(.3)
        plt.gca().spines["left"].set_alpha(.3)

        ax.set_xlabel('Message', fontsize=20)
        ax.set_ylabel('Sentiment', fontsize=20)
        ax.grid(alpha=.4)

        plt.title("Sentiment analysis: [-1:1] -> [negative:positive]")
        plt.legend()
        #plt.savefig(new_image_dir + 'line_history.png', dpi=400)
        #plt.clf()
        plt.show()

    def generatePDF(self):
        scatter = new_image_dir + 'line_history.png'
        heat = new_image_dir + 'hourly_heatmap.png'
        word = new_image_dir + 'wordcloud.png'
        pie = new_image_dir + 'pie.png'

        pdf = PdfFileWriter()

        # Using ReportLab Canvas to insert image into PDF
        scatterHeight = self.figureHeightPix
        pieHeight = self.figureHeightPix
        height = scatterHeight + pieHeight + self.heatmapHeight + self.wordHeight
        imgTemp = BytesIO()
        imgDoc = canvas.Canvas(imgTemp, pagesize=(self.pageWidth, height))

        scatterY = height - scatterHeight
        imgDoc.drawImage(scatter, 0, scatterY, width=self.pageWidth, height=scatterHeight)

        heatY = scatterY - self.heatmapHeight
        imgDoc.drawImage(heat, 100, heatY, width=self.pageWidth, height=self.heatmapHeight)

        wordY = heatY - self.wordHeight
        imgDoc.drawImage(word, 50, wordY, width=self.pageWidth, height=self.wordHeight)

        pieY = wordY - pieHeight
        imgDoc.drawImage(pie, 50, pieY, width=self.pageWidth, height=pieHeight)

        imgDoc.save()
        pdf.addPage(PdfFileReader(BytesIO(imgTemp.getvalue())).getPage(0))
        pdf.write(open("Conversation_analysis.pdf", "wb"))

        if sys.platform == "win32":
            os.startfile("Conversation_analysis.pdf")
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, "Conversation_analysis.pdf"])


if __name__ == "__main__":
    analysis = Analysis()
    conversations = analysis.getConversations()
    for i, conversationSrc in enumerate(conversations):
        print('Source ['+str(i)+']: '+ DIR[i])
    while True:
        chosen_src=input("Select Source of chat: ")
        try:
            val = int(chosen_src)
            if val < 0:  # if not a positive int print message and ask for input again
                print("Sorry, input must be a positive integer, try again")
                continue
            elif val > len(conversations)-1:
                print("Sorry, input must be smaller than the number of sources, try again")
                continue
            break
        except ValueError:
            print("Sorry, input must be an integer, try again")

    for j, conversation in enumerate(conversations[int(chosen_src)]):
        print('['+ str(j) +']  ' + conversation)
    while True:
        chosen_index = input("Select index of chat: ")
        try:
            val = int(chosen_index)
            if val < 0:  # if not a positive int print message and ask for input again
                print("Sorry, input must be a positive integer, try again")
                continue
            elif val > len(conversations[int(chosen_src)])-1:
                print("Sorry, input must be smaller than the number of chats in the chosen source, try again")
                continue
            break
        except ValueError:
            print("Sorry, input must be an integer, try again")

    while True:
        chosen_timezone = input("Enter your timezone ('EST', 'UTC', 'Etc/GMT+1' etc.). Enter 0 for all options: ")
        if chosen_timezone in pytz.all_timezones:
            break
        elif chosen_timezone == '0':
            print(pytz.all_timezones)
        else:
            print("Timezone not valid, try again")

    chosenPath = DIR[int(chosen_src)] + '/' + conversations[int(chosen_src)][int(chosen_index)]

    analysis.p = Parser(chosenPath, chosen_timezone)
    analysis.createScatterChart()
    analysis.createHeatmap()
    analysis.createWordcloud()
    analysis.createPieChart()
    analysis.generatePDF()
