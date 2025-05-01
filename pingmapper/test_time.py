from datetime import datetime, timezone, timedelta
import pytz

# Set the desired start date (e.g., January 1, 2000)
start_date = datetime(1989, 12, 31, 0, 0, 0, tzinfo=timezone.utc)

# Convert the datetime object to a Unix timestamp
unix_timestamp = start_date.timestamp()

# Given Unix time relative to the custom start date
custom_unix_time = 1110560328

# Convert the custom Unix time to a datetime object
converted_date = start_date + timedelta(seconds=custom_unix_time)

# Convert the UTC datetime to Eastern Time Zone
eastern = pytz.timezone("US/Eastern")
converted_date_eastern = converted_date.astimezone(eastern)

print("Custom Unix Start Time:", unix_timestamp)
print("Converted Date and Time:", converted_date_eastern)