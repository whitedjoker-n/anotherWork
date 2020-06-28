from futu import *
import pymysql
# import tushare
from datetime import datetime
from tqdm import tqdm

import tushare as ts


'''
获取futu 接口
'''
def getOpenQuoteContext():
    return  OpenQuoteContext(host="127.0.0.1", port=11111)



'''
连接sql云服务器
'''
def getSQLConnect():
    conn = pymysql.connect(host='58.87.83.244',
                       user='root',
                       password='hmt126899',
                       database='stock_game',
                       charset='utf8',
                       port=61481)
    return conn

'''
获取港股所有股票编号
'''
def HK_security():
    quote_ctx = getOpenQuoteContext()
    ret, data = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)

    if ret == RET_OK:
        HK_security_list = data["code"].tolist() +['HK.800000']
        return HK_security_list

    else:

        print("error:",data)

    quote_ctx.close()



'''
获取A股所有股票编号
'''
def CN_security():
    stock_df = ts.get_stock_basics()
    codes = list(stock_df.index)

    return codes



class DailyCrawler:

    def __init__(self,region, kTypes, start_time, end_time):


        self.region = region

        if self.region == "CN":
            self.codes = CN_security()
        elif self.region == "HK":
            self.codes = HK_security()

        self.kTypes = kTypes
        self.start_time = start_time
        self.end_time = end_time



    def HK_futu_api(self,quote_ctx,code, startTime, endTime,kType="K_DAY"):

        page_req_key = None
        counts = 0
        while True:
            ret, kline, prk = quote_ctx.request_history_kline(code, startTime, endTime, ktype=kType,
                                                            page_req_key=page_req_key)
            if counts == 0:
                try:
                    df = pd.DataFrame(kline)
                except:
                    df = None
                    print("code: {} has not been downloaed properly".format(code))
                    break


                counts += len(kline)
            else:
                df1 = pd.DataFrame(kline)
                df = df.append(df1, ignore_idex = True)
                counts += len(kline)
            page_req_key = prk
            if page_req_key == None:
                break

        return df, counts

    def CN_tushare_daily_api(self,code, startTime, endTime):

        df = ts.get_k_data(code, autype="hfq",start=startTime, end=endTime)
        counts = len(df)

        return df, counts


    def save_to_sql(self,conn,cursor,df,kType="K_DAY"):
        dfkeys = df.keys()
        dfvalueslist = df.values.tolist();
        # cursor = conn.cursor()
        key_sql = ','.join(dfkeys)
        value_sql = ','.join(['%s'] * df.shape[1])
        # insert_data_str = """ insert into %s (%s) values (%s)""" % ("k_line", key_sql, value_sql)

        # 插入语句，若数据已存在则更新数据
        if self.region == 'HK':
            insert_data_str = """ insert into %s (%s, %s) values (%s, '%s') ON DUPLICATE KEY UPDATE""" % (
        "k_line", key_sql, "type", value_sql, kType)
        elif self.region == "CN":
            insert_data_str = """ insert into %s (%s, %s) values (%s, '%s') ON DUPLICATE KEY UPDATE""" % (
        "k_line_tushare", key_sql, "type", value_sql, kType)
        update_str = ','.join([" {key} = VALUES({key})".format(key=key) for key in dfkeys])
        insert_data_str += update_str

        cursor.executemany(insert_data_str, dfvalueslist)
        conn.commit()



    def crawl_daily(self):

        now = datetime.now().strftime("%Y-%m-%d")
        conn = getSQLConnect()
        cursor = conn.cursor()
        self.start_time = self.start_time or now
        self.end_time = self.end_time or now

        # if self.startTime is None:
        #     self.startTime = now
        #
        # if self.end_time is None:
        #     self.end_time = now


        if self.region == "HK":
            quote_ctx = getOpenQuoteContext()
            for code in tqdm(self.codes):


                # if self.precheck_kline_data_from_sql(conn,cursor,code,startTime,endTime) is None:
                #     print("code {} already in sql".format(code))
                #     continue
                # else:
                #     startTime,endTime = self.precheck_kline_data_from_sql(conn,cursor,code,startTime,endTime)

                if not self.precheck_kline_data_from_sql_need_download(conn,cursor,code,self.start_time,self.end_time):
                    print("code {} already in sql".format(code))
                    continue
                else:
                    df, counts = self.HK_futu_api(quote_ctx, code, self.start_time, self.end_time)

                if df is None:
                    continue

                self.save_to_sql(conn, cursor, df)
                self.verfiy_kline_from_sql(conn, cursor, code, counts, self.start_time, self.end_time)



            cursor.close()
            conn.close()
            quote_ctx.close()

        elif self.region == "CN":
            for code in tqdm(self.codes):
                # if self.precheck_kline_data_from_sql(conn,cursor,code,startTime,endTime):
                #     continue
                # else:
                #     startTime,endTime = self.precheck_kline_data_from_sql(conn,cursor,code,startTime,endTime)

                if not self.precheck_kline_data_from_sql_need_download(conn,cursor,code,self.start_time,self.end_time):
                    print("code {} already in sql".format(code))
                    continue
                else:
                    df, counts = self.CN_tushare_daily_api(code, self.start_time, self.end_time)
                    self.save_to_sql(conn, cursor, df)
                    self.verfiy_kline_from_sql(conn, cursor, code, counts, self.start_time, self.end_time)
            cursor.close()
            conn.close()



    def precheck_kline_data_from_sql(self,conn,cursor,code,startTime,endTime,kType="K_DAY"):
        ''''
        等读表
         '''


        input_startTime = datetime.strptime(startTime,'%Y-%m-%d')
        input_endTime = datetime.strptime(endTime,'%Y-%m-%d')

        request_startTime = None
        request_endTime = None

        sql = "SELECT * FROM kline_record WHERE code = %s AND kline_type = %s "
        cursor.execute(sql, [code, kType,])
        results = cursor.fetchall()
        if len(results)==0 or results[0][3]==None :
            return startTime,endTime
        else:
            check_startTime = results[0][3]
            check_endTime = results[0][4]

            if input_startTime < check_startTime and input_endTime <= check_endTime:
                request_startTime = input_startTime
                request_endTime = check_startTime

                return request_startTime,request_endTime

            elif check_startTime<=input_startTime and input_endTime<=check_endTime:
                return None

            elif  check_startTime<= input_startTime and input_endTime> check_endTime:
                request_startTime = check_endTime
                request_endTime = input_endTime

                return request_startTime,request_endTime
            else:
                return check_endTime,input_endTime








        # return_counts = len(results)

        # if self.region == 'HK':
        #     sql = "SELECT * FROM k_line WHERE code = %s AND type = %s AND time_key >= %s AND time_key <= %s"
        # elif self.region =='CN':
        #     sql = "SELECT * FROM k_line_tushare WHERE code = %s AND type = %s AND date >= %s AND date <= %s"
        #
        # # cursor = conn.cursor()
        # cursor.execute(sql, [code, kType, startTime, endTime])
        # results = cursor.fetchall()
        # return_counts = len(results)
        #
        # if return_counts > 0:
        #     return True
        # else:
        #     return False


    def precheck_kline_data_from_sql_need_download(self,conn,cursor,code,startTime,endTime,kType="K_DAY"):
        ''''
        等读表
         '''

        input_startTime = datetime.strptime(startTime,'%Y-%m-%d')
        input_endTime = datetime.strptime(endTime,'%Y-%m-%d')

        sql = "SELECT * FROM kline_record WHERE code = %s AND kline_type = %s "
        cursor.execute(sql, [code, kType,])
        results = cursor.fetchall()
        if len(results)==0 or results[0][3]==None :
            return True
        else:
            check_startTime = results[0][3]
            check_endTime = results[0][4]
            if check_startTime<=input_startTime and input_endTime<=check_endTime:
                return False

            self.start_time = check_endTime if (input_endTime > check_endTime) else input_startTime
            self.end_time = input_endTime if (input_endTime > check_endTime) else check_startTime
            return True





        # return_counts = len(results)

        # if self.region == 'HK':
        #     sql = "SELECT * FROM k_line WHERE code = %s AND type = %s AND time_key >= %s AND time_key <= %s"
        # elif self.region =='CN':
        #     sql = "SELECT * FROM k_line_tushare WHERE code = %s AND type = %s AND date >= %s AND date <= %s"
        #
        # # cursor = conn.cursor()
        # cursor.execute(sql, [code, kType, startTime, endTime])
        # results = cursor.fetchall()
        # return_counts = len(results)
        #
        # if return_counts > 0:
        #     return True
        # else:
        #     return False


    def verfiy_kline_from_sql(self,conn,cursor,code, counts,startTime,endTime,kType="K_DAY"):

        if self.region == 'HK':
            sql = "SELECT * FROM k_line WHERE code = %s AND type = %s AND time_key >= %s AND time_key <= %s"
        elif self.region =='CN':
            sql = "SELECT * FROM k_line_tushare WHERE code = %s AND type = %s AND date >= %s AND date <= %s"

        # cursor = conn.cursor()
        cursor.execute(sql, [code, kType, startTime, endTime])
        results = cursor.fetchall()
        return_counts = len(results)

        if return_counts == counts:
            self.save_info(cursor,conn,code,kType,startTime,endTime)
            print("code {} kline from {} to {} has been uploaded to sql successfully".format(code,startTime,endTime))

        else:
            print("code {} kline from {} to {} has not been uploaded to sql successfully".format(code,startTime,endTime))


    def save_info(self,cursor,conn,code,kType,startTime,endTime):
        '''
        写表
        '''

        # keys = ['code','kline_type','start_time','end_time']
        # valueslist = [code,kType,startTime,endTime];

        sql= "INSERT INTO kline_record (code, kline_type, start_time,end_time) VALUES ('{}', '{}', '{}', '{}') \
                    ON DUPLICATE KEY UPDATE code = '{}', kline_type = '{}',start_time = '{}', end_time = '{}';".format(code,kType,startTime,endTime,code,kType,startTime,endTime)
        cursor.execute(sql)
        conn.commit()



if __name__ == "__main__":

    dc = DailyCrawler("HK", None, "2020-05-10", "2020-06-11")
    dc.crawl_daily()
