# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'scmiwlgi',
#         'USER': 'scmiwlgi',
#         'PASSWORD': 'TFP9YRYa1EmcciYEEBqsAsrSq9O9qiWV',
#         'HOST': 'isilo.db.elephantsql.com',
#         'PORT': '5432'
#     }
# }

import psycopg2

if __name__ == '__main__':

    try:
        conn = psycopg2.connect(
        database="scmiwlgi",
        user="scmiwlgi",
        password="TFP9YRYa1EmcciYEEBqsAsrSq9O9qiWV",
        host="isilo.db.elephantsql.com",
        port="5432",
        )
        print("connect successfull")
    except:
        print("Can't connect db")


    pakid = 1
    cursor = conn.cursor()
    #sql = "UPDATE WEBSERVER_PACKAGE SET STATUS = 'Packing' WHERE PACKAGE_ID = '" +  str(pakid) + "';"
    #cursor.execute(sql)

    item_id = 1
    count  = 1
    description = 1

    sql2 = "SELECT * FROM WEBSERVER_PACKAGE WHERE PRODUCT_NAME = '" + str(item_id) + "' AND COUNT = '" + str(count) + "' AND DESCRIPTION = '" + str(description) + "';"

    try:
        cursor.execute(sql2)
        result = cursor.fetchall()
        for row in result:
            Whid = row[0]
            x = row[1]
            b = row[2]
            c = row[3]
            y = row[4]
            s = row[5]
            u = row[6]
            v = row[7]
            m = row[8]
            k = row[9]
            q = row[10]
            o = row[11]
            print("Whiid= %s, x= %s, y= %s",(Whid,x,b,c,y,s,u,v,m,k,q,o))
    except:
        print("Error, no warehouse")
