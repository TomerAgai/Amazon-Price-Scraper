from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
from scraper import search_amazon, get_prices_for_asin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from db import create_connection, initialize_db, insert_search_result, get_past_searches, count_searches_today

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///search_history.db'
db = SQLAlchemy(app)

AMAZON_SITES = {
    "com": "https://www.amazon.com",
    "co.uk": "https://www.amazon.co.uk",
    "de": "https://www.amazon.de",
    "ca": "https://www.amazon.ca"
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET', 'POST'])
def search():

    conn = create_connection('search_history.db')
    search_date = datetime.now().strftime('%Y-%m-%d')
    search_count = count_searches_today(conn, search_date)
    print("search count = ", search_count)

    if search_count >= 10:
        return render_template('error.html', message='Daily searches cap reached. Consider upgrading to the premium service in order to search for more items.')

    if request.method == 'POST':
        search_query = request.form['search_query']
        results = search_amazon(search_query, "com")

       # Insert search results into the database
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for result in results:
            result["timestamp"] = timestamp
            insert_search_result(conn, result)
        conn.close()

        return render_template('search_results.html', results=results)
    else:
        asin = request.args.get('asin')
        if asin:
            prices = {}
            for site in AMAZON_SITES:
                result = search_amazon(None, site, asin=asin)
                if result:
                    prices[site] = result[0]
            return render_template('prices.html', prices=prices, asin=asin)
        else:
            return redirect(url_for('index'))


@app.route('/prices', methods=['GET'])
def prices():
    asin = request.args.get('asin')
    results = get_prices_for_asin(asin)
    return render_template('prices.html', results=results)


@app.route('/past_searches', methods=['GET'])
def past_searches():
    conn = create_connection('search_history.db')
    past_searches = get_past_searches(conn)
    conn.close()
    return render_template('past_searches.html', past_searches=past_searches)


if __name__ == '__main__':
    conn = create_connection('search_history.db')
    initialize_db(conn)
    conn.close()
    app.run(debug=True)
