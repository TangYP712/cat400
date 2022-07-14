from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from datetime import date
from datetime import datetime
from matplotlib.font_manager import json_dump
from werkzeug.utils import secure_filename
import uuid as uuid
import os
import MySQLdb.cursors
import re
import random
import joblib
import numpy as np
import pandas as pd
import json

# from recommendation import *

import matplotlib.pyplot as plt
import plotly.express as px
import plotly
from chart_studio import plotly
import plotly.graph_objs as go

from statsmodels.tsa.arima.model import ARIMA
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)
app.secret_key = 'many random bytes'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'system_db'

UPLOAD_FOLDER = 'static/images/profile_pic'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

UPLOAD_CSV_FOLDER = 'static/csv'
app.config['UPLOAD_CSV_FOLDER'] = UPLOAD_CSV_FOLDER

UPLOAD_PRODUCT_FOLDER = 'static/images/product_images'
app.config['UPLOAD_PRODUCT_FOLDER'] = UPLOAD_PRODUCT_FOLDER

mysql = MySQL(app)


@app.route('/')
def landing():
    return render_template('index.html')

@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        user_id = session['id']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT customer_id FROM customer WHERE user_id=%s", (user_id,))
        cusId = cur.fetchone()
        cur.close()
        cusId = cusId['customer_id']

        # Get all information for dashboard
        # 1. Get sales by brand for doughnut
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders.orders_id, SUM(orders_quantity) AS quantity, product.product_brand FROM orders INNER JOIN orders_details ON orders.orders_id = orders_details.orders_id\
            INNER JOIN product ON orders_details.product_id = product.product_id WHERE orders.customer_id=%s GROUP BY product.product_brand", (cusId,))
        d_cat = cur.fetchall()
        cur.close()
        if d_cat:
            do_labels = []
            do_values = []
            for do in d_cat:
                x = do['product_brand']
                y = do['quantity']
                y = str(y)
                do_labels += [x]
                do_values += [y]

        # 2. Get sales by categories for pie chart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders.orders_id, SUM(orders_quantity) AS quantity, product.product_category FROM orders INNER JOIN orders_details ON orders.orders_id = orders_details.orders_id\
            INNER JOIN product ON orders_details.product_id = product.product_id WHERE orders.customer_id=%s GROUP BY product.product_category", (cusId,))
        s_cat = cur.fetchall()
        cur.close()
        if s_cat:
            pie_labels = []
            pie_values = []
            for i in s_cat:
                x = i['quantity']
                x = str(x)
                y = i['product_category']
                pie_labels += [y]
                pie_values += [x]

        # 3. Get spending for line chart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_month, orders_year, SUM(orders_amount) AS amount FROM orders WHERE customer_id=%s GROUP BY orders_year, orders_month ORDER BY orders_month, orders_year", (cusId,))
        spending = cur.fetchall()
        cur.close()
        if spending:
            line_labels = []
            line_values = []
            for i in spending:
                m_s = i['orders_month']
                y_s = i['orders_year']
                x = str(m_s)+"/"+str(y_s)
                y = i['amount']
                y = float(y)
                line_labels += [x]
                line_values += [y]

        # 4. Get current and previous rfm rank
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT customer_id, rfm_rank, (LAG(rfm_rank, 1) OVER(PARTITION BY customer_id ORDER BY record_date)) AS previous_rfm_rank FROM behavioural_data WHERE customer_id=%s ORDER BY record_date DESC", (cusId,))
        rfm = cur.fetchone()
        cur.close()
        if rfm:
            p_rank = rfm['previous_rfm_rank']
            c_rank = rfm['rfm_rank']
            diff = p_rank - c_rank
            diff_rank = " "
            diff_rank = changes(diff)
            # for RFM line chart plotting
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT record_date, rfm_rank FROM behavioural_data WHERE customer_id=%s ORDER BY record_date", (cusId,))
            rows = cur.fetchall()
            cur.close()
            labels, values = graph_plotting(rows)

        if d_cat and s_cat and spending and rfm:
            return render_template('home.html', c_rank=c_rank, diff_rank=diff_rank, labels=json.dumps(labels), values=json.dumps(values), pie_labels=json.dumps(pie_labels), pie_values=json.dumps(pie_values), do_labels=json.dumps(do_labels), do_values=json.dumps(do_values), line_labels=json.dumps(line_labels), line_values=json.dumps(line_values))
        elif d_cat and s_cat and spending:
            return render_template('home.html', pie_labels=json.dumps(pie_labels), pie_values=json.dumps(pie_values), do_labels=json.dumps(do_labels), do_values=json.dumps(do_values), line_labels=json.dumps(line_labels), line_values=json.dumps(line_values))
        else:
            return render_template('home.html')
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/sellercomplete')
def completedOrders():
    if 'loggedin' in session:
        selId = getSellerId()
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM orders WHERE seller_id=%s AND orders_status='Completed' ORDER BY orders_date DESC", (selId,))
        orders = cur.fetchall()
        cur.close()
        return render_template('seller_completeOrders.html', orders = orders)
    else:
        return redirect(url_for('login'))


@app.route('/seller_viewOrders/<orderId>')
def completed_orders_details(orderId):
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT product.product_image AS p_img, product.product_name AS p_name, product.product_brand AS p_brand, \
            product.product_price AS p_price, orders_details.orders_quantity AS o_quantity, orders_details.orders_total_amount AS o_total \
                FROM orders_details INNER JOIN product ON orders_details.product_id = product.product_id WHERE orders_details.orders_id = %s', (orderId,))
        orders = cur.fetchall()
        cur.close()
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_no, orders_date, orders_amount, orders_status, orders_shipping_details FROM orders WHERE orders_id=%s", (orderId,))
        order = cur.fetchone()
        cur.close()
        return render_template('seller_viewOrders.html', orderedList = orders, order = order)
    else:
        return redirect(url_for('login'))


@app.route('/sellerpending')
def pendingOrders():
    if 'loggedin' in session:
        selId = getSellerId()
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM orders WHERE seller_id=%s AND orders_status='In Progress' OR orders_status='Shipped' ORDER BY orders_date DESC", (selId,))
        orders = cur.fetchall()
        cur.close()
        return render_template('seller_pendingOrders.html', orders = orders)
    else:
        return redirect(url_for('login'))


# For pending orders
@app.route('/ordersdetails/<ordersId>')
def orders_details(ordersId):
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT product.product_image AS p_img, product.product_name AS p_name, product.product_brand AS p_brand, product.product_shade AS p_shade, \
            product.product_price AS p_price, orders_details.orders_quantity AS o_quantity, orders_details.orders_total_amount AS o_total \
                    FROM orders_details INNER JOIN product ON orders_details.product_id = product.product_id WHERE orders_details.orders_id = %s', (ordersId,))
        orders = cur.fetchall()
        cur.close()

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_no, orders_date, orders_amount, orders_status, orders_shipping_details FROM orders WHERE orders_id=%s", (ordersId,))
        order = cur.fetchone()
        cur.close()

        return render_template('seller_manageOrders.html', order = order, orderedList = orders)
    else:
        return redirect(url_for('login'))


@app.route('/testing', methods=['GET','POST'])
def manage_orders():
    if request.method == "POST":
        status_to_update = request.form['status']
        ordersno = request.form['orderno']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE orders SET orders_status=%s WHERE orders_no=%s", (status_to_update, ordersno,))
        mysql.connection.commit()
        cur.close()

        flash("Order status has been successfully updated!")
        return redirect(url_for('pendingOrders'))





@app.route('/adminhome')
def adminhome():
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customer")
        customer_row = cur.fetchall()
        cur.close
        return render_template('admin_home.html', customer_row = customer_row)
    else:
        return redirect(url_for('login'))

@app.route('/adminhome', methods=['GET','POST'])
def update_customer():
    if request.method == "POST":
        user_id = request.form['user_id']
        name_to_update = request.form['name']
        email_to_update = request.form['email']
        contact_to_update = request.form['contact_no']
        gender_to_update = request.form['gender']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("UPDATE customer SET customer_name=%s, customer_email=%s, customer_contact=%s, customer_gender=%s WHERE user_id=%s", (name_to_update, email_to_update, contact_to_update, gender_to_update, user_id,))
        mysql.connection.commit()

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("UPDATE user SET user_email=%s WHERE user_id=%s", (email_to_update, user_id,))
        mysql.connection.commit()

        flash("Profile has been successfully updated!")
    return redirect(url_for('adminhome'))

@app.route('/adminhome/<cusId>', methods=['GET','POST'])
def delete_customer(cusId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("DELETE FROM user WHERE user_id=%s",(cusId,))
    mysql.connection.commit()
    cur.close
    return redirect(url_for('adminhome'))

@app.route('/manageseller')
def manageseller():
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM seller")
        seller_row = cur.fetchall()
        cur.close
        return render_template('admin_manageseller.html', seller_row = seller_row)
    else:
        return redirect(url_for('login'))

@app.route('/manageseller', methods=['GET','POST'])
def update_seller():
    if request.method == "POST":
        user_id = request.form['user_id']
        name_to_update = request.form['name']
        email_to_update = request.form['email']
        contact_to_update = request.form['contact_no']
        gender_to_update = request.form['gender']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("UPDATE seller SET seller_name=%s, seller_email=%s, seller_contact=%s, seller_gender=%s WHERE user_id=%s", (name_to_update, email_to_update, contact_to_update, gender_to_update, user_id,))
        mysql.connection.commit()

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("UPDATE user SET user_email=%s WHERE user_id=%s", (email_to_update, user_id,))
        mysql.connection.commit()

        flash("Profile has been successfully updated!")

    return redirect(url_for('manageseller'))

@app.route('/manageseller/<sellerId>', methods=['GET','POST'])
def delete_seller(sellerId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("DELETE FROM user WHERE user_id=%s",(sellerId,))
    mysql.connection.commit()
    cur.close
    return redirect(url_for('manageseller'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'user_email' in request.form and 'user_password' in request.form and 'role' in request.form:
        # Create variables for easy access
        email = request.form['user_email']
        password = request.form['user_password']
        role = request.form['role']
        # Check if account exists using MySQL
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM user WHERE user_email = %s AND user_password = %s AND user_role = %s', (email, password, role,))
        account = cur.fetchone()
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['user_id']
            session['useremail'] = account['user_email']
            session['userrole'] = account['user_role']

            if session['userrole'] == "Customer":
                return redirect(url_for('home'))
            elif session['userrole'] == "Seller":
                return redirect(url_for('seller_dashboard'))
            elif session['userrole'] == "Admin":
                return redirect(url_for('adminhome'))           
        else:
            flash("Login unsuccessful. Incorrect email / password / role or Account doesn't exist.")
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and 'user_name' in request.form and 'user_email' in request.form and 'user_password' in request.form and 'confirm_user_password' in request.form and 'user_contact' in request.form and 'gender' in request.form and 'role' in request.form:
        # Create variables for easy access
        name = request.form['user_name']
        email = request.form['user_email']
        password = request.form['user_password']
        password2 = request.form['confirm_user_password']
        contact = request.form['user_contact']
        gender = request.form['gender']
        role = request.form['role']

        # Check if account exists using MySQL
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM user WHERE user_email = %s', (email,))
        account = cur.fetchone()
        # If account exists show error and validation checks
        if account:
            flash("This email has been used to register an account before.")
        elif not re.match(r'[A-Za-z0-9]+', name):
            flash("Please provide a valid name.")
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash("Invalid email address.")
        elif password != password2:
            flash("Passwords do not match.")
        else:
            cur.execute('INSERT INTO user VALUES (NULL, %s, %s, %s)', (email, password, role,))
            mysql.connection.commit()
            cur.close()

            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * from user where user_email = %s", (email,))
            row = cur.fetchone()
            user_id = row['user_id']
            cur.close()

            default_pic = 'default_profile_pic.jpg'

            if role == "Customer":
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute('INSERT INTO customer (customer_name, customer_password, customer_email, customer_contact, customer_gender, user_id, customer_profile_picture) VALUES (%s, %s, %s, %s, %s, %s, %s)', (name, password, email, contact, gender, user_id, default_pic,))
                mysql.connection.commit()
                cur.close()          
            elif role == "Seller":
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute('INSERT INTO seller VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)', (name, password, email, contact, gender, user_id, default_pic))
                mysql.connection.commit()
                cur.close()

            flash("You have successfully registered an account.")

    elif request.method == 'POST':
        flash("Please fill in all required fields")

    return render_template('register.html')



@app.route('/logout')
def logout():
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('useremail', None)
   session.pop('userrole', None)
   return redirect(url_for('login'))



@app.route('/purchase/<ordersId>')
def purchase_details(ordersId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT product.product_image AS p_img, product.product_name AS p_name, product.product_brand AS p_brand, product.product_shade AS p_shade,\
                product.product_price AS p_price, product.product_id AS p_id, orders_details.orders_quantity AS o_quantity, orders_details.orders_total_amount AS o_total \
                FROM orders_details INNER JOIN product ON orders_details.product_id = product.product_id \
                WHERE orders_details.orders_id = %s', (ordersId,))
    ordered_items = cur.fetchall()
    cur.close()

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT orders_no, orders_date, orders_amount, orders_payment, orders_status, orders_shipping_details, voucher_applied FROM orders WHERE orders_id = %s", (ordersId,))
    ordered_info = cur.fetchone()
    cur.close()

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT product_id, rating_score, rating_review FROM rating WHERE orders_id = %s", (ordersId,))
    ordered_rating = cur.fetchall()
    cur.close()
    return render_template('purchaseitems.html', orderedList = ordered_items, orderedInfo = ordered_info, orderedRating = ordered_rating)


@app.route('/purchase')
def purchase():
    if 'loggedin' in session:
        user_id = session['id']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM customer WHERE user_id = %s', (user_id,))
        customer = cur.fetchone()
        cur.close()
        if customer:
            cusId = customer['customer_id']
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM rating WHERE customer_id = %s', (cusId,))
            cRating = cur.fetchone()
            cur.close()

            if cRating:
                rc = product_recommender(cusId,5,3)
                prod = []
                prod_rat = []
                for i in rc:
                    prod_id = i[0]
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("SELECT * FROM product WHERE product_id=%s", (prod_id,))
                    re = cur.fetchall()
                    cur.close()
                    prod += re
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("SELECT product_id, rating_score, rating_review, rating_time FROM rating WHERE product_id=%s", (prod_id,))
                    rat = cur.fetchall()
                    cur.close()
                    prod_rat += rat
            else:
                prod = []
                prod_rat = []
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("SELECT product_id, SUM(orders_quantity) AS quantity FROM orders_details GROUP BY product_id ORDER BY SUM(orders_quantity) DESC LIMIT 3")
                top_prod = cur.fetchall()
                cur.close()
                for j in top_prod:
                    prod_id = j['product_id']
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("SELECT * FROM product WHERE product_id=%s", (prod_id,))
                    re = cur.fetchall()
                    cur.close()
                    prod += re
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("SELECT product_id, rating_score, rating_review FROM rating WHERE product_id=%s", (prod_id,))
                    rat = cur.fetchall()
                    cur.close()
                    prod_rat += rat


            # Get customer purchase history
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM orders WHERE customer_id = %s ORDER BY orders_date DESC', (cusId,))
            orders = cur.fetchall()
            cur.close()

            if orders:
                return render_template('purchase.html', prod = prod, prod_rat = prod_rat, ordersList = orders)
            else:
                return render_template('purchase.html', prod = prod, prod_rat = prod_rat)
    else:
        return redirect(url_for('login'))


def product_recommender(user, num_neighbors, num_recommendation):

    cur = mysql.connection.cursor()
    cur.execute("SELECT customer_id, product_id, rating_score FROM rating")
    ratings = cur.fetchall()

    df = pd.DataFrame(ratings)
    df.columns = ['userID','productID','rating']

    df = pd.pivot_table(df,index='productID',columns='userID',values='rating')
    df = df.fillna(0)

    df1 = df.copy()

    number_neighbors = num_neighbors
    
    knn = NearestNeighbors(metric='cosine', algorithm='brute')
    knn.fit(df.values)
    distances, indices = knn.kneighbors(df.values, n_neighbors=number_neighbors)
    
    user_index = df.columns.tolist().index(user)
    
    for m,t in list(enumerate(df.index)):
        if df.iloc[m, user_index] == 0:
            sim_products = indices[m].tolist()
            product_distances = distances[m].tolist()
            
            if m in sim_products:
                id_product = sim_products.index(m)
                sim_products.remove(m)
                product_distances.pop(id_product)
                
            else:
                sim_products = sim_products[:number_neighbors-1]
                product_distances = product_distances[:number_neighbors-1]
            
            # product_similarty = 1 - product_distance
            product_similarity = [1-x for x in product_distances]
            product_similarity_copy = product_similarity.copy()
            nominator = 0
        
            for s in range(0, len(product_similarity)):
                # check if the rating of a similar product is zero
                if df.iloc[sim_products[s], user_index] == 0:
                    # if the rating is zero, ignore the rating and the similarity in calculating the predicted rating
                    if len(product_similarity_copy) == (number_neighbors - 1):
                        product_similarity_copy.pop(s)
                    
                    else:
                        product_similarity_copy.pop(s-(len(product_similarity)-len(product_similarity_copy)))
                        
                else:
                    nominator = nominator + product_similarity[s]*df.iloc[sim_products[s],user_index]
                    
            if len(product_similarity_copy) > 0:
                if sum(product_similarity_copy) > 0:
                    predicted_r = nominator/sum(product_similarity_copy)
                else:
                    predicted_r = 0
            else:
                predicted_r = 0
                
            df1.iloc[m,user_index] = predicted_r

    recommended_products = []
    
    for m in df[df[user] == 0].index.tolist():
        index_df = df.index.tolist().index(m)
        predicted_rating = df1.iloc[index_df, df1.columns.tolist().index(user)]
        recommended_products.append((m, predicted_rating))
        

    sorted_rp = sorted(recommended_products, key=lambda x:x[1], reverse=True)

    rank = 1
    
    for recommended_product in sorted_rp[:num_recommendation]:
        print('{}: Product {} - predicted rating: {}'.format(rank, recommended_product[0], recommended_product[1]))
        rank = rank + 1
    
    return sorted_rp[:num_recommendation]






@app.route('/shopface')
def face_product():
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        returnRow = cur.execute("SELECT * FROM product WHERE product_stock > 10 AND product_category = 'Foundation' or product_category = 'Concealer' or product_category = 'Moisturizer' or product_category = 'Bronzer'")
        if returnRow > 0:
            products = cur.fetchall()
            cur.close()
            prodfrating = []
            for x in products:
                prodid = x['product_id']
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("SELECT product_id, rating_score, rating_review, rating_time FROM rating WHERE product_id=%s", (prodid,))
                prodf_rating = cur.fetchall()
                cur.close()
                prodfrating += prodf_rating
            return render_template('shopface.html', products = products, prodfrating = prodfrating)
    else:
        return redirect(url_for('login'))

@app.route('/shopeyes')
def eye_product():
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        returnRow = cur.execute("SELECT * FROM product WHERE product_stock > 10 AND product_category = 'Eyebrow' or product_category = 'Eyeshadow' or product_category = 'Eyeliner' or product_category = 'Eye Primer' or product_category = 'Mascara'")
        if returnRow > 0:
            products = cur.fetchall()
            cur.close()
            proderating = []
            for x in products:
                prodid = x['product_id']
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("SELECT product_id, rating_score, rating_review, rating_time FROM rating WHERE product_id=%s", (prodid,))
                prode_rating = cur.fetchall()
                cur.close()
                proderating += prode_rating
            return render_template('shopeyes.html', products = products, proderating = proderating)
    else:
        return redirect(url_for('login'))

@app.route('/shoplips')
def lips_product():
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        returnRow = cur.execute("SELECT * FROM product WHERE product_stock > 10 AND product_category = 'Lipstick' or product_category = 'Lip Balm' or product_category = 'Lip Gloss'")
        if returnRow > 0:
            products = cur.fetchall()
            cur.close()
            prodlrating = []
            for x in products:
                prodid = x['product_id']
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("SELECT product_id, rating_score, rating_review, rating_time FROM rating WHERE product_id=%s", (prodid,))
                prodl_rating = cur.fetchall()
                cur.close()
                prodlrating += prodl_rating
            return render_template('shoplips.html', products = products, prodlrating = prodlrating)
    else:
        return redirect(url_for('login'))

@app.route('/cart')
def display_cart():
    msg = ""
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer where user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cusId = row['customer_id']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT cart.product_id AS prod_id, cart.quantity AS prod_qty, cart.total_price AS prod_tprc, product.product_image AS prod_img, product.product_brand AS prod_brand,\
        product.product_name AS prod_name, product.product_shade AS prod_shade, product.product_price AS prod_price FROM cart \
        INNER JOIN product ON cart.product_id = product.product_id WHERE customer_id=%s", (cusId,))
    cart = cur.fetchall()
    cur.close()
    if cart:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT SUM(total_price) AS total_prc FROM cart WHERE customer_id=%s", (cusId,))
        prc = cur.fetchone()
        cur.close()
        return render_template('cart.html', cart=cart, prc=prc)
    else:
        msg = "Your Shopping Cart is Empty."
        return render_template('cart.html', msg = msg)







@app.route('/shopface', methods=['GET', 'POST'])
@app.route('/shopeyes', methods=['GET', 'POST'])
@app.route('/shoplips', methods=['GET', 'POST'])
def add_to_wishlist():
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer where user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cus_id = row['customer_id']

    if request.method == 'POST':
        product_id = request.form['id']
        # check if the item is already in the wishlist
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM wishlist WHERE customer_id=%s AND product_id=%s", (cus_id, product_id,))
        row = cur.fetchall()
        cur.close()
        if row:
            flash("This item is already in your wishlist.")
        else:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO wishlist (customer_id, product_id) VALUES (%s, %s)", (cus_id, product_id,))
            mysql.connection.commit()
            cur.close()
            flash("This item is successfully added to your wishlist.")
        return redirect(request.referrer)
    
@app.route('/wishlist')
def show_wishlist():
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer where user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cus_id = row['customer_id']
    # get wishlist items
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT product.product_id AS pid, product.product_brand AS pb, product.product_name AS pn, product.product_price AS pp, product.product_image AS pi \
        FROM product INNER JOIN wishlist ON product.product_id = wishlist.product_id WHERE customer_id=%s", (cus_id,))
    wl = cur.fetchall()
    cur.close()
    if wl:
        return render_template('wishlist.html', wishlist = wl)
    else:
        msg = "There is nothing in your wishlist."
        return render_template('wishlist.html', msg = msg)

@app.route('/wishlist/<id>')
def delete_wishlist_items(id):
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer where user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cus_id = row['customer_id']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("DELETE FROM wishlist WHERE customer_id=%s AND product_id=%s", (cus_id, id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('show_wishlist'))

@app.route('/checkout')
def check_out():
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer where user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cusId = row['customer_id']

    # Get customer info
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM customer WHERE customer_id=%s", (cusId,))
    cus = cur.fetchone()
    cur.close()

    # Get cart items
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT cart.product_id AS prod_id, cart.quantity AS prod_qty, cart.total_price AS prod_tprc, product.product_image AS prod_img, product.product_brand AS prod_brand,\
        product.product_name AS prod_name, product.product_shade AS prod_shade, product.product_price AS prod_price FROM cart \
        INNER JOIN product ON cart.product_id = product.product_id WHERE customer_id=%s", (cusId,))
    prod = cur.fetchall()
    cur.close()
    if prod:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT SUM(total_price) AS total_prc FROM cart WHERE customer_id=%s", (cusId,))
        prc = cur.fetchone()
        cur.close()

    # Check if the user got any vouchers claimed at the same day of making order
    dateplay = date.today()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT DISTINCT prize_description FROM prize WHERE gameplay_date=%s AND customer_id=%s",(dateplay, cusId,))
    row2 = cur.fetchall()
    cur.close()

    if row2:
        return render_template('checkout.html', prod=prod, cus=cus, prc=prc, voucher=row2)
    else:
        return render_template('checkout.html', prod=prod, cus=cus, prc=prc)

@app.route('/placeorder', methods=['POST'])
def place_order():
    if 'loggedin' in session:
        user_id = session['id']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customer WHERE user_id=%s",(user_id,))
        row = cur.fetchone()
        cus_id = row['customer_id']
        cur.close()
        if request.method == "POST":
            order_amount = request.form['actual_order_total']
            voucher = request.form['voucher']

            r_name = request.form['name']
            r_phone = request.form['phone']
            r_add1 = request.form['shippingadd1']
            r_add2 = request.form['shippingadd2']
            r_postcode = request.form['postcode']
            r_city = request.form['city']
            r_state = request.form['state']
            shipping_details = r_name + " " + r_phone + " " + r_add1 + " " + r_add2 + " " + r_postcode + " " + r_city + " " + r_state

            n = random.randint(100000,999999)
            order_num = "INV_"+ str(n)
            date_created = date.today()
            day = date_created.day
            month = date_created.month
            year = date_created.year
            dateplay = date.today()

            if voucher == "5% Off":
                payment = float(order_amount) * 0.95
            elif voucher == "10% Off":
                payment = float(order_amount) * 0.90
            elif voucher == "15% Off":
                payment = float(order_amount) * 0.85
            elif voucher == "20% Off":
                payment = float(order_amount) * 0.80
            elif voucher == "25% Off":
                payment = float(order_amount) * 75
            elif voucher == "No Voucher":
                payment = float(order_amount)

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO orders (orders_no, orders_date, orders_day, orders_month, orders_year, orders_amount, voucher_applied, orders_payment, customer_id, orders_status, orders_shipping_details, orders_rated, seller_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (order_num, date_created, day, month, year, order_amount, voucher, payment, cus_id, "In Progress", shipping_details, 0, 1,))
            mysql.connection.commit()
            cur.close()

            # Delete voucher which had been applied
            if voucher != "No Voucher":
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM prize WHERE prize_description=%s AND gameplay_date=%s AND customer_id=%s ORDER BY prize_id ASC LIMIT 1", (voucher, dateplay, cus_id,))
                mysql.connection.commit()
                cur.close()

            # Get orders id
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM orders WHERE orders_no=%s",(order_num,))
            row = cur.fetchone()
            orders_id = row['orders_id']
            cur.close()

            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT product_id, quantity, total_price FROM cart WHERE customer_id=%s", (cus_id,))
            prod = cur.fetchall()
            cur.close()

            for i in prod:
                product_id = i['product_id']
                quantity = i['quantity']
                item_price = i['total_price']
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO orders_details (orders_id, product_id, orders_quantity, orders_total_amount) VALUES (%s, %s, %s, %s)", (orders_id, product_id, quantity, item_price,))
                mysql.connection.commit()
                cur.close()
                # Delete cart item
                cur = mysql.connection.cursor()
                cur.execute("DELETE FROM cart WHERE customer_id=%s", (cus_id,))
                mysql.connection.commit()
                cur.close()
                # Update stock in product database table
                # Get original stock
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("SELECT * FROM product WHERE product_id=%s", (product_id,))
                prod_stock = cur.fetchone()
                cur.close()
                ori_stock = prod_stock['product_stock']
                updated_stock = int(ori_stock) - int(quantity)
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("UPDATE product SET product_stock=%s WHERE product_id=%s", (updated_stock,product_id,))
                mysql.connection.commit()
                cur.close()            
            return render_template('vieworder.html')
    else:
        return redirect(url_for('login'))


@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'loggedin' in session:
        user_id = session['id']

        if request.method == "POST":
            name_to_update = request.form['name']
            email_to_update = request.form['email']
            contact_to_update = request.form['contact_no']
            gender_to_update = request.form['gender']
            add1_to_update = request.form['shippingadd1']
            add2_to_update = request.form['shippingadd2']
            postcode_to_update = request.form['postcode']
            city_to_update = request.form['city']
            state_to_update = request.form['state']

            if request.files['profile_pic']:
                profilepic_to_update = request.files['profile_pic']            
                # Grab image name
                pic_filename = secure_filename(profilepic_to_update.filename)
                # Set UUID
                pic_name = str(uuid.uuid1()) + "_" + pic_filename
                # Save the image
                profilepic_to_update.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                # Change it to a string to save to db
                profilepic_to_update = pic_name

                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("UPDATE customer SET customer_profile_picture=%s WHERE user_id=%s", (profilepic_to_update, user_id,))
                mysql.connection.commit()

            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE customer SET customer_name=%s, customer_email=%s, customer_contact=%s, customer_gender=%s, customer_add1=%s, customer_add2=%s, \
                customer_postal=%s, customer_city=%s, customer_state=%s WHERE user_id=%s", (name_to_update, email_to_update, contact_to_update, gender_to_update, add1_to_update,
                add2_to_update, postcode_to_update, city_to_update, state_to_update, user_id,))
            mysql.connection.commit()
            cur.close()

            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE user SET user_email=%s WHERE user_id=%s", (email_to_update, user_id,))
            mysql.connection.commit()
            cur.close()

            flash("Profile has been successfully updated!")
    
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customer WHERE user_id = %s",(user_id,))
        profile = cur.fetchone()
        cur.close()
        return render_template('profile.html', profile = profile)
    else:
        return redirect(url_for('login'))

@app.route('/spin', methods=['GET','POST'])
def spinandwin():
    if 'loggedin' in session:
        user_id = session['id']
        today_date = date.today()

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM gameplay WHERE gameplay_date=%s AND user_id=%s", (today_date, user_id,))
        row = cur.fetchone()
        cur.close()

        if row:
            isplayed = row['gameplay_isplayed']
            if isplayed == 0:
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("SELECT * FROM gameplay WHERE gameplay_date=%s AND user_id=%s", (today_date, user_id,))
                row = cur.fetchone()
                chances = row['gameplay_chances']
                cur.close()
            elif isplayed == 1:
                chances = 0
        else:
            chances = 3
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO gameplay (gameplay_date, gameplay_isplayed, gameplay_chances, user_id) VALUES (%s, %s, %s, %s)", (today_date, 0, 3, user_id,))
            mysql.connection.commit()
            cur.close()

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customer WHERE user_id=%s", (user_id,))
        row2 = cur.fetchone()
        cus_id = row2['customer_id']
        cur.close()

        # Get gameplay id
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM gameplay WHERE gameplay_date=%s AND user_id=%s", (today_date, user_id,))
        row3 = cur.fetchone()
        gameid = row3['gameplay_id']
        cur.close()

        if request.method == "POST":
            p = request.form['prize']
            c = request.form['ch']

            if c != "" and p != "":
                new_c = c
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("UPDATE gameplay SET gameplay_chances=%s WHERE user_id=%s AND gameplay_date=%s", (new_c, user_id, today_date,))
                mysql.connection.commit()
                cur.close()
                
                if p != "Thank You" and p != "":
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("INSERT INTO prize (prize_description, gameplay_id, gameplay_date, customer_id) VALUES (%s,%s,%s,%s)", (p, gameid, today_date, cus_id,))
                    mysql.connection.commit()
                    cur.close()
                
                if c == "0":
                    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cur.execute("UPDATE gameplay SET gameplay_isplayed=%s WHERE user_id=%s AND gameplay_date=%s", (1, user_id, today_date,))
                    mysql.connection.commit()
                    cur.close()
                
                flash("Successfully collected your voucher! Use it in your next purchase.")
                return redirect(request.referrer)
            elif c == "" and p == "":
                return redirect(request.referrer)
        return render_template('spin.html', chances = chances)
    else:
        return redirect(url_for('login'))

@app.route('/rate/<ordersId>')
def rate(ordersId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT orders.orders_id AS o_id, product.product_id AS p_id, product.product_image AS p_img, product.product_name AS p_name, \
        product.product_brand AS p_brand, product.product_shade AS p_shade, orders.orders_no AS o_no, orders.orders_status AS o_status, orders.orders_shipping_details AS o_sd FROM orders \
            INNER JOIN orders_details ON orders.orders_id = orders_details.orders_id \
                INNER JOIN product ON orders_details.product_id = product.product_id WHERE orders.orders_id = %s', (ordersId,))
    orders = cur.fetchall()
    cur.close()
    return render_template('rating.html', orderedList = orders)


@app.route('/rating/<ordersId>', methods=['GET','POST'])
def rate_product(ordersId):
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM customer WHERE user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cus_id = row['customer_id']

    if request.method == "POST":
        p_id = request.form.getlist('p_id[]')
        p_star = request.form.getlist('rating[]')
        p_review = request.form.getlist('p_review[]')

        created_date = date.today()

        for i in range(len(p_id)) and range(len(p_star)) and range(len(p_review)):
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO rating (customer_id, orders_id, product_id, rating_score, rating_review, rating_time) VALUES (%s, %s, %s, %s, %s, %s)", (cus_id, ordersId, str(p_id[i]), str(p_star[i]), str(p_review[i]), created_date,))
            mysql.connection.commit()
            cur.close()
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("UPDATE orders SET orders_rated=%s WHERE orders_id=%s", (1, ordersId,))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('purchase'))

@app.route('/viewrating/<ordersId>')
def view_rating(ordersId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT product.product_image AS p_img, product.product_name AS p_name, product.product_brand AS p_brand, orders.orders_no AS o_no, rating.rating_score AS r_score, \
        rating.rating_review AS r_review FROM rating INNER JOIN orders ON orders.orders_id = rating.orders_id INNER JOIN product ON product.product_id = rating.product_id \
        WHERE rating.orders_id=%s", (ordersId,))
    orderedList = cur.fetchall()
    cur.close()
    return render_template('viewrating.html', orderedList = orderedList)

@app.route('/avatar')
def avatar():
    if 'loggedin' in session:
        return render_template('avatar.html')
    else:
        return redirect(url_for('login'))

@app.route('/avatar', methods=['GET','POST'])
def avatar_cart():
    if 'loggedin' in session:
        user_id = session["id"]
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT customer_id FROM customer WHERE user_id=%s",(user_id,))
        cid = cur.fetchone()
        cur.close()
        cusId = cid['customer_id']

        if request.method == 'POST':
            product_name = request.form['product_name']
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT product_id FROM product WHERE product_shortname=%s", (product_name,))
            row = cur.fetchone()
            cur.close()
            p_id = row['product_id']

            # check if the item is already in the wishlist
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT * FROM wishlist WHERE customer_id=%s AND product_id=%s", (cusId, p_id,))
            row = cur.fetchall()
            cur.close()
            
            if row:
                flash("This item is already in your wishlist.")
            else:
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("INSERT INTO WISHLIST (customer_id, product_id) VALUES (%s,%s)", (cusId, p_id,))
                mysql.connection.commit()
                cur.close()
                flash("This item is successfully added to your wishlist.")
            
            return redirect(url_for('avatar'))
    else:
        return redirect(url_for('login'))

def getCustomerId():
    user_id = session["id"]
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer WHERE user_id=%s",(user_id,))
    cus = cur.fetchone()
    cur.close()
    return cus['customer_id']


def getSellerId():
    user_id = session["id"]
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT seller_id FROM seller WHERE user_id=%s",(user_id,))
    sel = cur.fetchone()
    cur.close()
    return sel['seller_id']


@app.route('/sellerdashboard')
def seller_dashboard():
    if 'loggedin' in session:
        selId = getSellerId()

        msg = ""
        # Get monthly sales amount
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_month, orders_year, SUM(orders_amount) AS TotalSales FROM orders WHERE seller_id=%s GROUP BY orders_month, orders_year ORDER BY orders_year, orders_month DESC", (selId,))
        m_sales = cur.fetchall()
        cur.close()
        if m_sales:
            if len(m_sales) > 1:
                latest_sales = m_sales[0]['TotalSales']
                latest_sales = f"{latest_sales:.2f}"
                previous_sales = m_sales[1]['TotalSales']
                sales_increment = float(latest_sales) - float(previous_sales)
                sales_increment_percentage = (float(sales_increment) / float(previous_sales)) * 100
                percentage = f"{sales_increment_percentage:.2f}"
                percentage = float(percentage)
            if len(m_sales) == 1:
                latest_sales = m_sales[0]['TotalSales']
                latest_sales = f"{latest_sales:.2f}"
                previous_sales = 0.00
                sales_increment = float(latest_sales) - float(previous_sales)
                # sales_increment_percentage = (sales_increment / previous_sales) * 100
                # percentage = f"{sales_increment_percentage:.2f}"
                percentage = float(100)
        else:
            msg = "No Record Found"

        # Get monthly orders
        msg2 = ""
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_month, orders_year, COUNT(orders_no) AS OrdersCount FROM orders WHERE seller_id=%s GROUP BY orders_month, orders_year ORDER BY orders_year, orders_month DESC", (selId,))
        m_orders = cur.fetchall()
        cur.close()
        if m_orders:
            if len(m_orders) > 1:
                latest_orders = m_orders[0]['OrdersCount']
                previous_orders = m_orders[1]['OrdersCount']
                orders_diff = latest_orders - previous_orders
                orders_increment_percentage = (orders_diff / previous_orders) * 100
                orders_percentage = f"{orders_increment_percentage:.2f}"
            if len(m_orders) == 1:
                latest_orders = m_orders[0]['OrdersCount']
                previous_orders = 0
                orders_diff = latest_orders
                orders_percentage = float(100)
        else:
            msg2 = "No Record Found"

        # Get pending orders count
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT COUNT(orders_no) AS POrdersNum FROM orders WHERE seller_id=%s AND orders_status='In Progress' OR orders_status='Shipped'", (selId,))
        p_orders = cur.fetchone()
        cur.close()
        if p_orders:
            pon = p_orders['POrdersNum']

        # Get complete orders count
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT COUNT(orders_no) AS COrdersNum FROM orders WHERE seller_id=%s AND orders_status = 'Completed'", (selId,))
        c_orders = cur.fetchone()
        cur.close()
        if c_orders:
            con = c_orders['COrdersNum']

        # Get sales by categories for pie chart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT SUM(orders_quantity) AS quantity, product.product_category FROM orders_details \
            INNER JOIN product ON orders_details.product_id = product.product_id INNER JOIN orders \
                ON orders_details.orders_id = orders.orders_id WHERE orders.seller_id=%s GROUP BY product.product_category", (selId,))
        s_cat = cur.fetchall()
        cur.close()
        if s_cat:
            p_labels = []
            p_values = []
            for i in s_cat:
                x = i['quantity']
                x = str(x)
                y = i['product_category']
                p_labels += [y]
                p_values += [x]

        # Get sales by product brand for doughnut chart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT SUM(orders_quantity) AS quantity, product.product_brand FROM orders_details \
            INNER JOIN product ON orders_details.product_id = product.product_id INNER JOIN orders \
                ON orders_details.orders_id = orders.orders_id WHERE orders.seller_id=%s GROUP BY product.product_brand", (selId,))
        b_cat = cur.fetchall()
        cur.close()
        if b_cat:
            d_labels = []
            d_values = []
            for d in b_cat:
                x = d['product_brand']
                y = d['quantity']
                y = str(y)
                d_labels += [x]
                d_values += [y]
    
        # Get total sales for each and every month
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_month, orders_year, SUM(orders_amount) AS TotalSales FROM orders WHERE seller_id=%s GROUP BY orders_month, orders_year ORDER BY orders_year, orders_month", (selId,))
        sales = cur.fetchall()
        cur.close()
        if sales:
            labels = []
            values = []
            for i in sales:
                m = i['orders_month']
                y = i['orders_year']
                x = str(m)+"/"+str(y)
                y = i['TotalSales']
                y = str(y)
                labels += [x]
                values += [y]
        
        if m_sales and m_orders and p_orders and c_orders and s_cat and b_cat and sales:
            return render_template('seller_dashboard.html', lsale=latest_sales, msale=percentage, msg=msg, msg2=msg2, mo=latest_orders, op=orders_percentage, pon=pon, con=con, p_labels=json.dumps(p_labels), p_values=json.dumps(p_values), d_labels=json.dumps(d_labels), d_values=json.dumps(d_values), labels=json.dumps(labels), values=json.dumps(values))
        elif p_orders and c_orders and s_cat and b_cat and sales:
            return render_template('seller_dashboard.html', msg=msg, msg2=msg2, pon=pon, con=con, p_labels=json.dumps(p_labels), p_values=json.dumps(p_values), d_labels=json.dumps(d_labels), d_values=json.dumps(d_values), labels=json.dumps(labels), values=json.dumps(values))
        else:
            return render_template('seller_dashboard.html', msg=msg, msg2=msg2)
    else:
        return redirect(url_for('login'))


@app.route('/sprofile', methods=['GET','POST'])
def sprofile():
    if 'loggedin' in session:
        user_id = session['id']

        if request.method == "POST":
            name_to_update = request.form['name']
            email_to_update = request.form['email']
            contact_to_update = request.form['contact_no']
            gender_to_update = request.form['gender']

            if request.files['profile_pic']:
                profilepic_to_update = request.files['profile_pic']            
                # Grab image name
                pic_filename = secure_filename(profilepic_to_update.filename)
                # Set UUID
                pic_name = str(uuid.uuid1()) + "_" + pic_filename
                # Save the image
                profilepic_to_update.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                # Change it to a string to save to db
                profilepic_to_update = pic_name

                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("UPDATE seller SET seller_profile_picture=%s WHERE user_id=%s", (profilepic_to_update, user_id,))
                mysql.connection.commit()
                cur.close()
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE seller SET seller_name=%s, seller_email=%s, seller_contact=%s, seller_gender=%s WHERE user_id=%s", (name_to_update, email_to_update, contact_to_update, gender_to_update, user_id,))
            mysql.connection.commit()
            cur.close()

            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE user SET user_email=%s WHERE user_id=%s", (email_to_update, user_id,))
            mysql.connection.commit()
            cur.close()

            flash("Profile has been successfully updated!")
    
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM seller WHERE user_id = %s",(user_id,))
        profile = cur.fetchone()
        return render_template('seller_profile.html', profile = profile)
    else:
        return redirect(url_for('login'))


@app.route('/customers')
def my_customer():
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customer")
        row = cur.fetchall()
        cur.close()
        return render_template('seller_mycustomer.html', mycus = row)
    else:
        return redirect(url_for('login'))

@app.route('/viewordersdetails/<orderId>')
def get_customer_purchases_details(orderId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT product.product_image AS p_img, product.product_name AS p_name, \
        product.product_brand AS p_brand, product.product_price AS p_price, orders_details.orders_quantity AS o_quantity, \
            orders_details.orders_total_amount AS o_total FROM orders_details INNER JOIN product ON orders_details.product_id = product.product_id \
                WHERE orders_details.orders_id = %s', (orderId,))
    orders = cur.fetchall()
    cur.close()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id, orders_no, orders_date, orders_status, orders_amount, orders_status, orders_shipping_details FROM orders WHERE orders_id=%s", (orderId,))
    order = cur.fetchone()
    cur.close()
    return render_template('seller_viewCustomerOrders.html', orders = orders, order = order)


def get_customer_purchases(cusId):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM orders WHERE customer_id=%s ORDER BY orders_date DESC", (cusId,))
    cp = cur.fetchall()
    cur.close()
    return cp


@app.route('/classification/<cusId>', methods=['GET', 'POST'])
def classification(cusId):
    if 'loggedin' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM customer WHERE customer_id=%s", (cusId,))
        profile = cur.fetchone()
        cur.close()

        cp = get_customer_purchases(cusId)

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM behavioural_data WHERE customer_id=%s ORDER BY record_date DESC", (cusId,))
        row = cur.fetchone()
        cur.close()
        if row:
            n1 = row['recency']
            n2 = row['frequency']
            n3 = row['monetary']
            n4 = row['r_rank_norm']
            n5 = row['f_rank_norm']
            n6 = row['m_rank_norm']
            n7 = row['rfm_score']
            record_date = row['record_date']

            model_in = joblib.load('classification_model.pkl')
            current_rank = model_in.predict(np.array([[n1, n2, n3, n4, n5, n6, n7]]))
            rfmrank = current_rank[0]

            # save classification result
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE behavioural_data SET rfm_rank = %s WHERE customer_id = %s AND record_date = %s", (rfmrank, cusId, record_date,))
            mysql.connection.commit()
            cur.close()


        # get current and previous rfm rank and compute changes
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT customer_id, rfm_rank, (LAG(rfm_rank, 1) OVER(PARTITION BY customer_id ORDER BY record_date)) AS previous_rfm_rank FROM behavioural_data WHERE customer_id=%s ORDER BY record_date DESC", (cusId,))
        t = cur.fetchone()
        cur.close()
        if t:
            p_rank = t['previous_rfm_rank']
            c_rank = t['rfm_rank']
            if p_rank == None:
                p_rank = 0

            diff = p_rank - c_rank
            diff_rank = " "
            diff_rank = changes(diff)

        # for graph plotting
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT record_date, rfm_rank FROM behavioural_data WHERE customer_id=%s ORDER BY record_date", (cusId,))
        rows = cur.fetchall()
        cur.close()

        if rows:
            labels, values = graph_plotting(rows)

        # Get sales by categories for pie chart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders.orders_id, SUM(orders_quantity) AS quantity, product.product_category FROM orders INNER JOIN orders_details ON orders.orders_id = orders_details.orders_id\
            INNER JOIN product ON orders_details.product_id = product.product_id WHERE orders.customer_id=%s GROUP BY product.product_category", (cusId,))
        s_cat = cur.fetchall()
        cur.close()
        if s_cat:
            pie_labels = []
            pie_values = []
            for i in s_cat:
                x = i['quantity']
                x = str(x)
                y = i['product_category']
                pie_labels += [y]
                pie_values += [x]
        
        #Get spending for line chart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT orders_month, orders_year, SUM(orders_amount) AS amount FROM orders WHERE customer_id=%s GROUP BY orders_year, orders_month ORDER BY orders_month, orders_year", (cusId,))
        spending = cur.fetchall()
        cur.close()
        if spending:
            line_labels = []
            line_values = []
            for i in spending:
                m_s = i['orders_month']
                y_s = i['orders_year']
                x = str(m_s)+"/"+str(y_s)
                y = i['amount']
                y = float(y)
                line_labels += [x]
                line_values += [y]
        
        if row and cp and t and rows and s_cat and spending:
            return render_template('classification.html', profile=profile, cp=cp, labels=labels, values=values, cr=rfmrank, t=diff, diff_rank=diff_rank, pie_labels=json.dumps(pie_labels), pie_values=json.dumps(pie_values), line_labels=json.dumps(line_labels), line_values=json.dumps(line_values))
        elif cp and s_cat and spending:
            return render_template('classification.html', profile=profile, cp=cp, pie_labels=json.dumps(pie_labels), pie_values=json.dumps(pie_values), line_labels=json.dumps(line_labels), line_values=json.dumps(line_values))
        else:
            return render_template('classification.html', profile=profile)
    else:
        return redirect(url_for('login'))

def changes(difference):
    if difference == 0:
        return "No Change"
    elif difference == 1 or difference == -1:
        return "Little Change"
    elif difference == 2 or difference == -2:
        return "Medium Change"
    elif difference == 3 or difference == -3:
        return "Large Change"
    elif difference == 4 or difference == -4:
        return "Very Large Change"

def graph_plotting(row):  
    labels = []
    values = []
    for i in row:
        x = i['record_date']
        y = i['rfm_rank']
        labels += [x]
        values += [y]
    return labels, values


@app.route('/classification', methods=['GET', 'POST'])
def upload_csv():
    uploaded_csv = request.files['myfile']
    if uploaded_csv.filename != "":
        #set file path
        file_path = os.path.join(app.config['UPLOAD_CSV_FOLDER'], uploaded_csv.filename)
        uploaded_csv.save(file_path)
        parseCSV(file_path)
    return redirect(request.referrer)

def parseCSV(filePath):
    col_names = ['customer_id', 'record_date', 'recency', 'frequency', 'monetary', 'r_rank_norm', 'f_rank_norm', 'm_rank_norm', 'rfm_score']
    csvData = pd.read_csv(filePath, names=col_names, header=0)
    for index, row in csvData.iterrows():
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("INSERT INTO behavioural_data (customer_id, record_date, recency, frequency, monetary, r_rank_norm, f_rank_norm, m_rank_norm, rfm_score) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (row['customer_id'], row['record_date'], row['recency'], row['frequency'], row['monetary'], row['r_rank_norm'], row['f_rank_norm'], row['m_rank_norm'], row['rfm_score'],))
        # value = (row['Customer_ID'], row['Record_Date'], row['Recency'], row['Frequency'], row['Monetary'], row['R_rank_norm'], row['F_rank_norm'], row['M_rank_norm'], row['RFM_Score'], row['Rank'])
        # cur.execute(sql, value, if_exists='append')
        mysql.connection.commit()
        cur.close()







@app.route('/prediction', methods=['GET','POST'])
def sales_prediction():
    if 'loggedin' in session:
        selId = getSellerId()

        if request.method == "POST":
            sD = request.form['startDay']
            eD = request.form['endDay']
            startDate = datetime.strptime(sD, '%Y-%m-%d').date()
            endDate = datetime.strptime(eD, '%Y-%m-%d').date()
            dayDiff = endDate - startDate
            daysCount = dayDiff.days

            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT orders_date, SUM(orders_amount) AS sales_amount FROM orders WHERE seller_id=%s GROUP BY orders_date", (selId,))
            sales = cur.fetchall()
            cur.close()
            if sales:
                sales_df = pd.DataFrame(sales)
                sales_df.columns = ['Date','Sales Amount']
                df2 = sales_df.set_index('Date')
                model = ARIMA(df2['Sales Amount'], order=(0,0,1))
                model = model.fit()

                index_future_dates = pd.date_range(start=startDate, end=endDate)
                pred = model.predict(start=0, end=0+daysCount, typ='levels').rename('ARIMA Prediction')
                pred.index = index_future_dates

                td = []
                timeseries_dates = sales_df['Date'].values.tolist()
                for i in timeseries_dates:
                    td += [str(i)]

                for j in pred.index:
                    k = j.strftime("%Y-%m-%d")
                    td += [k]

                sales_amount = sales_df["Sales Amount"].values.tolist()
                for sa in pred:
                    sales_amount += [f"{sa:.2f}"]

                return render_template('seller_prediction.html', sales_amount=sales_amount, timeseries_dates=td, startDate=startDate, endDate=endDate)
            else:
                return render_template('seller_prediction.html')
        else:
            td = []
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("SELECT orders_date, SUM(orders_amount) AS sales_amount FROM orders WHERE seller_id=%s GROUP BY orders_date", (selId,))
            sales = cur.fetchall()
            cur.close()
            if sales:
                sales_df = pd.DataFrame(sales)
                sales_df.columns = ['Date','Sales Amount']
                timeseries_dates = sales_df['Date'].values.tolist()
                for i in timeseries_dates:
                    td += [str(i)]
                sales_amount = sales_df['Sales Amount'].values.tolist()
                return render_template('seller_prediction.html', sales_amount=sales_amount, timeseries_dates=td)
            else:
                return render_template('seller_prediction.html')
    else:
        return redirect(url_for('login'))





















    
@app.route('/manageproducts')
def manage_product():
    if 'loggedin' in session:
        selId = getSellerId()
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM product WHERE seller_id=%s", (selId,))
        row = cur.fetchall()
        cur.close()
        if row:
            return render_template('seller_manageProduct.html', row=row)
        else:
            return render_template('seller_manageProduct.html')
    else:
        return redirect(url_for('login'))

@app.route('/manageproducts', methods=['GET','POST'])
def seller_add_new_product():
    selId = getSellerId()
    if request.method == "POST":
        p_code = request.form['product_code']
        p_brand = request.form['product_brand']
        p_name = request.form['product_name']
        p_sname = request.form['product_shortname']
        p_desc = request.form['product_description']
        p_shade = request.form['product_shade']
        p_price = request.form['product_price']
        p_cat = request.form['product_category']
        p_stock = request.form['product_stock']
       
        p_pic = request.files['product_pic']
        # Grab image name
        p_pic_filename = secure_filename(p_pic.filename)
        # Set UUID
        p_pic_name = str(uuid.uuid1()) + "_" + p_pic_filename
        # Save the image
        p_pic.save(os.path.join(app.config['UPLOAD_PRODUCT_FOLDER'], p_pic_name))
        # Change it to a string to save to db
        p_pic = p_pic_name

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("INSERT INTO product (product_code,product_brand,product_name,product_shortname,product_shade,product_description,product_price,product_image,product_category,product_stock,seller_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (p_code,p_brand,p_name,p_sname,p_shade,p_desc,p_price,p_pic,p_cat,p_stock,selId,))
        mysql.connection.commit()
        cur.close()
    return redirect(request.referrer)

@app.route('/deleteproduct/<prodID>')
def seller_delete_product(prodID):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("DELETE FROM product WHERE product_id=%s", (prodID,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('manage_product'))

@app.route('/editproducts', methods=['GET','POST'])
def seller_edit_product():
    if 'loggedin' in session:
        if request.method == "POST":
            ep_id = request.form['eproduct_id']
            ep_code = request.form['eproduct_code']
            ep_brand = request.form['eproduct_brand']
            ep_name = request.form['eproduct_name']
            ep_sname = request.form['eproduct_shortname']
            ep_desc = request.form['eproduct_description']
            ep_shade = request.form['eproduct_shade']
            ep_price = request.form['eproduct_price']
            ep_cat = request.form['eproduct_category']
            ep_stock = request.form['eproduct_stock']
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE product SET product_code=%s, product_brand=%s, product_name=%s, product_shortname=%s, product_shade=%s, product_description=%s, product_price=%s, product_category=%s, product_stock=%s WHERE product_id=%s", (ep_code,ep_brand,ep_name,ep_sname,ep_shade,ep_desc,ep_price,ep_cat,ep_stock,ep_id,))
            mysql.connection.commit()
            cur.close()

            if request.files['eproduct_pic']:
                ep_pic = request.files['eproduct_pic']            
                # Grab image name
                eppic_filename = secure_filename(ep_pic.filename)
                # Set UUID
                eppic_name = str(uuid.uuid1()) + "_" + eppic_filename
                # Save the image
                ep_pic.save(os.path.join(app.config['UPLOAD_PRODUCT_FOLDER'], eppic_name))
                # Change it to a string to save to db
                ep_pic = eppic_name

                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute("UPDATE product SET product_image=%s WHERE product_id=%s", (ep_pic, ep_id,))
                mysql.connection.commit()

        return redirect(request.referrer)
    else:
        return redirect(url_for('login'))











@app.route('/wishlist', methods=['GET','POST'])
@app.route('/cart', methods=['GET','POST'])
def add_to_cart():
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer WHERE user_id=%s", (user_id,))
    cusId = cur.fetchone()
    cur.close()
    cusId = cusId['customer_id']

    if request.method == 'POST':
        pid = request.form['id']
        pprc = request.form['price']
        pqty = request.form['quantity']

        # Check if the product is already in cart
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM cart WHERE customer_id=%s AND product_id=%s", (cusId, pid,))
        row = cur.fetchone()
        cur.close()
        # If yes, then update the quantity and total price
        if row:
            ori_q = row['quantity']
            new_q = ori_q + int(pqty)
            new_p = new_q * float(pprc)
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("UPDATE cart SET quantity=%s, total_price=%s WHERE customer_id=%s AND product_id=%s", (new_q, new_p, cusId, pid,))
            mysql.connection.commit()
            cur.close()
        else:
            tprc = int(pqty) * float(pprc)
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute("INSERT INTO cart (customer_id, product_id, quantity, total_price) VALUES (%s,%s,%s,%s)", (cusId, pid, pqty, tprc,))
            mysql.connection.commit()
            cur.close()

        return redirect(request.referrer)

@app.route('/empty')
def empty_cart():
    try:
        user_id = session['id']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT customer_id FROM customer WHERE user_id=%s", (user_id,))
        cusId = cur.fetchone()
        cur.close()
        cusId = cusId['customer_id']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("DELETE FROM cart WHERE customer_id=%s", (cusId,))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('display_cart'))
    except Exception as e:
        print(e)

@app.route('/delete/<string:id>')
def delete_cart_item(id):
    user_id = session['id']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT customer_id FROM customer where user_id=%s", (user_id,))
    row = cur.fetchone()
    cur.close()
    cusId = row['customer_id']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("DELETE FROM cart WHERE customer_id=%s AND product_id=%s", (cusId, id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('display_cart'))

if __name__ == "__main__":
    app.run(debug=True)