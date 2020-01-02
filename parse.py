import os
import json
import datetime
from collections import OrderedDict
import pytz
from ftfy import fix_text


class Parser:
    def __init__(self, participantPath, own_timezone):
        thread_dir=participantPath + '/'
        assert os.path.isdir(thread_dir), "Not a correct directory"
        assert own_timezone in pytz.all_timezones, "Not a correct timezone"
        self.timezone = pytz.timezone(own_timezone)
        message_files = [thread_dir + ms_file for ms_file in os.listdir(thread_dir) if ms_file.endswith('.json')]
        self.messages = []
        assert message_files, "No conversation files."
        for ms in message_files:
            with open(ms, 'r') as read_file:
                ms_json = json.load(read_file)
                self.participants = [fix_text(name["name"]) for name in ms_json["participants"]]
                self.messages += ms_json["messages"]
        self.messages_by_user = {}
        for user in self.participants:
            self.messages_by_user[user] = [ms for ms in self.messages if fix_text(ms["sender_name"]) == user]

    def getListOfDates(self, user):
        timestamp_ms = [time["timestamp_ms"] for time in self.messages_by_user[user]]
        return [datetime.datetime.fromtimestamp(ts / 1000).astimezone(self.timezone) for ts in timestamp_ms]

    def get_messages_by_date_of(self, user):
        all_messages_by_user = self.messages_by_user[user]
        timestamp_ms = [message["timestamp_ms"] for message in all_messages_by_user]
        dates = [datetime.datetime.fromtimestamp(ts / 1000).astimezone(self.timezone).date() for ts in timestamp_ms]
        messages = [message.get('content') for message in all_messages_by_user]
        return dict(zip(dates, messages))

    def get_line_chart_data(self):
        dates = {}
        for user in self.participants:
            days = self.getListOfDates(user)
            days = [day.date() for day in days]
            dates[user] = {}
            temp = {}
            for day in days:
                try:
                    temp[day] += 1
                except KeyError:
                    temp[day] = 1
            dates[user] = OrderedDict(sorted(temp.items()))
        return dates

    def get_heatmap_data(self):
        timeDay = {}
        days = [i for i in range(7)]
        for i, user in enumerate(self.participants):
            times = self.getListOfDates(user)
            by_day = []
            total = []
            for j, day in enumerate(days):
                timeh = [t.hour for t in times if t.weekday() == day]
                grouped_by_hour = [0] * 24
                averaged_by_hour = []
                for hour in timeh:
                    grouped_by_hour[hour] += 1
                for h in grouped_by_hour:
                    if (len(timeh) != 0):
                        averaged_by_hour.append(h/len(times))
                    else:
                        averaged_by_hour.append(0)
                by_day.append(averaged_by_hour)
            timeDay[user] = by_day
        return timeDay


    def get_first_5_messages(self):
        messages = [message['content'] for message in self.messages[:5]]
        return messages

    def get_all_messages_for_wordcloud(self):
        joined = {}

        for user in self.participants:
            messages = []
            filtered = []
            for ms in self.messages_by_user[user]:
                message = ms.get('content')
                if message is not None:
                    messages += [fix_text(spms) for spms in message.split() if len(spms) > 5]

            joined[user] = (" ").join(messages)
        return joined

    def get_num_messages_of_all_users(self):
        num_messages = {}
        for user in self.participants:
            num_messages[user] = len(self.messages_by_user[user])
        return num_messages

    def get_num_messages_of(self, user):
        num_messages = len(self.messages_by_user[user])
        return num_messages

    def get_num_words_of_all_users(self):
        num_words = {}
        for user in self.participants:
            num_words[user] = 0
            messages = [ms.get('content') for ms in self.messages_by_user[user]]
            for message in messages:
                if message is not None:
                    num_words[user] += len(fix_text(message).split())
        return num_words

    def get_num_words_of(self, user):
        num_words = 0
        messages = [ms.get('content') for ms in self.messages_by_user[user]]
        for message in messages:
            if message is not None:
                num_words += len(fix_text(message).split())
        return num_words

    def get_average_message_length_of_all_users(self):
        avg_message_length = {}
        for user in self.participants:
            num_messages = self.get_num_messages_of(user)
            num_words = self.get_num_words_of(user)
            if num_messages is not 0:
                avg_message_length[user] = num_words / num_messages
            else:
                avg_message_length[user] = 0
        return avg_message_length

    def get_average_message_length_of(self, user):
        num_messages = self.get_num_messages_of(user)
        num_words = self.get_num_words_of(user)
        if num_messages is not 0:
            avg_message_length = num_words / num_messages
        else:
            avg_message_length = 0
        return avg_message_length

    def get_data_for_conversation_starter(self):
        def func(x):
            return x.get('timestamp_ms')
        messages = sorted(self.messages, key=func)

        times_initiated_by_user = dict(zip(self.participants, [0] * len(self.participants)))

        prevTimeInHours = messages[0].get('timestamp_ms') / 3600000
        dt = 0
        for i, content in enumerate(messages):
            user = fix_text(content.get('sender_name'))
            time_now = content.get('timestamp_ms') / 3600000
            if i > 0:
                dt = time_now - prevTimeInHours
            if dt > 24:
                times_initiated_by_user[fix_text(content.get('sender_name'))] += 1
            prevTimeInHours = time_now
        return times_initiated_by_user
