# YouTube Channel Migration

This application allows you to migrate YouTube channel data to both MongoDB and a SQL database. It uses the YouTube Data API v3 to retrieve channel details and provides options to store the data in MongoDB and a SQL database.

## Prerequisites

Before running the application, make sure you have the following:

- Python 3.x installed on your system.
- The required Python packages installed. You can install them using the following command:
```
pip install google-api-python-client pymongo mysql-connector-python sqlalchemy streamlit pandas
```
- A YouTube Data API v3 key. You can obtain the key by creating a project in the Google Developers Console and enabling the YouTube Data API.

## Usage

1. Open a terminal or command prompt.

2. Clone or download the project files.

3. Install the required Python packages as mentioned in the Prerequisites section.

4. Replace `<Your YouTube API Key>` in the code with your actual YouTube Data API key.

5. Replace `<Your MySQL Password>` in the code with your actual MySQL password.

6. Open the terminal or command prompt and navigate to the project directory.

7. Run the following command to start the application:
```
streamlit run project1.py
```

8. The application will open in a web browser.

9. Enter the YouTube channel ID in the input field and click "Enter".

10. The application will display the channel details including the title, description, number of subscribers, total views, and total videos.

11. If you want to migrate the channel data, check the "Migrate this channel" checkbox.

12. The channel data will be stored in MongoDB and the SQL database.

13. Additional data visualization features are available to analyze the migrated data.

14. You can view the stored data in MongoDB and the SQL database using the respective tools or query the SQL database using the provided SQL statements.

15. To stop the application, press `Ctrl + C` in the terminal or command prompt.

Note: Make sure you have MongoDB and a MySQL database server running on your system.

Feel free to modify the code according to your specific requirements and database configurations.

That's it! You can now use the application to migrate YouTube channel data and visualize it using Streamlit's data visualization features.