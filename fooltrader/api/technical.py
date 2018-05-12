# -*- coding: utf-8 -*-

import pandas as pd

from fooltrader.api import quote
import datetime


def ma(security_item, start_date, end_date, level='day', fuquan='qfq', source='163', window=5,
       col=['close', 'volume', 'turnover'], return_all=False, return_col=True):
    """
    calculate ma.

    Parameters
    ----------
    security_item : SecurityItem or str
        the security item,id or code
    start_date : TimeStamp str or TimeStamp
        start date
    end_date : TimeStamp str or TimeStamp
        end date
    fuquan : str
        {"qfq","hfq","bfq"},default:"qfq"
    source : str
        the data source,{'163','sina'},default: '163'
    level : str or int
        the kdata level,{1,5,15,30,60,'day','week','month'},default : 'day'
    window : int
        the ma window,default : 5
    col : list
        the column for calculating,['close', 'volume', 'turnover'],default:['close', 'volume', 'turnover']

    return_all : bool
        whether return all the kdata values,default:False

    return_col : bool
        whether return the calculating col too,default:True

    Returns
    -------
    DataFrame

    """
    df = quote.get_kdata(security_item, fuquan=fuquan, start_date=start_date, end_date=end_date, source=source,
                         level=level)
    df_col = df.loc[:, col]

    df_result = df_col.rolling(window=window, min_periods=window).mean()
    df_result.columns = ["{}_ma{}".format(item, window) for item in col]
    if return_all:
        df_result = pd.concat([df, df_result], axis=1)
    elif return_col:
        df_result = pd.concat([df_col, df_result], axis=1)
    return df_result


def ema(security_item, start_date, end_date, level='day', fuquan='qfq', source='163', window=12, col=['close'],
        return_all=False, return_col=True):
    """
    calculate ema.

    Parameters
    ----------
    security_item : SecurityItem or str
        the security item,id or code
    start_date : TimeStamp str or TimeStamp
        start date
    end_date : TimeStamp str or TimeStamp
        end date
    fuquan : str
        {"qfq","hfq","bfq"},default:"qfq"
    source : str
        the data source,{'163','sina'},default: '163'
    level : str or int
        the kdata level,{1,5,15,30,60,'day','week','month'},default : 'day'
    window : int
        the ma window,default : 12
    col : list
        the column for calculating,['close', 'volume', 'turnover'],default:['close']

    return_all : bool
        whether return all the kdata values,default:False

    return_col : bool
        whether return the calculating col too,default:True

    Returns
    -------
    DataFrame

    """
    df = quote.get_kdata(security_item, fuquan=fuquan, start_date=start_date, end_date=end_date, source=source,
                         level=level)

    df_col = df.loc[:, col]
    df_result = df_col.ewm(span=window, adjust=False, min_periods=window).mean()
    df_result.columns = ["{}_ema{}".format(item, window) for item in col]
    if return_all:
        df_result = pd.concat([df, df_result], axis=1)
    elif return_col:
        df_result = pd.concat([df_col, df_result], axis=1)

    return df_result


def macd(security_item, start_date, end_date, level='day', fuquan='qfq', source='163', slow=26, fast=12, n=9,
         return_all=False, return_col=True):
    """
    calculate macd.

    Parameters
    ----------
    security_item : SecurityItem or str
        the security item,id or code
    start_date : TimeStamp str or TimeStamp
        start date
    end_date : TimeStamp str or TimeStamp
        end date
    fuquan : str
        {"qfq","hfq","bfq"},default:"qfq"
    source : str
        the data source,{'163','sina'},default: '163'
    level : str or int
        the kdata level,{1,5,15,30,60,'day','week','month'},default : 'day'
    slow : int
        the slow ma window,default : 26
    fast : list
        the fast ma window,default : 12

    return_all : bool
        whether return all the kdata values,default:False

    return_col : bool
        whether return the calculating col too,default:True

    Returns
    -------
    DataFrame

    """

    ema_fast = ema(security_item, start_date, end_date, level=level, fuquan=fuquan, source=source, window=fast,
                   return_all=return_all, return_col=return_col)

    ema_slow = ema(security_item, start_date, end_date, level=level, fuquan=fuquan, source=source, window=slow,
                   return_all=return_all, return_col=return_col)

    result = ema_fast.copy()
    result["close_ema{}".format(slow)] = ema_slow["close_ema{}".format(slow)]

    result['diff'] = result["close_ema{}".format(fast)] - result["close_ema{}".format(slow)]
    result['dea'] = result['diff'].ewm(span=n, adjust=False).mean()
    result['macd'] = (result['diff'] - result['dea']) * 2

    return result

def newhighergenerator(start_date,fuquan='qfq',source='163',period=20):

    baseindex = 'index_sh_000001'
    df = quote.get_kdata(baseindex,start_date=start_date,source=source)
    #df = quote.get_kdata('index_sh_000001',start_date='2017-05-10',source='163')
    dh = pd.DataFrame(0,index=df.index,columns=['total'])      #暂时只添加total，后续需要添加各个市场total
    #stocklist = quote.get_security_list(security_type='stock', mode='simple')
    stocklist = quote.get_security_list(security_type='stock',start='600000',end='600030', mode='simple')
    for _, item in stocklist.iterrows():
        print("caculating {}".format(item.id))
        for ts in dh.index:
            if((ts-datetime.datetime.strptime(item.listDate,'%Y-%m-%d')).days<period):
                dh.at[ts,item.id] = 0
            else:
                ds = quote.get_kdata(item.id,fuquan=fuquan)
                indexlist = list(ds['timestamp'])
                tsstr = ts.strftime('%Y-%m-%d')
                if(tsstr in indexlist):
                    pos = list(ds['timestamp']).index(ts.strftime('%Y-%m-%d'))
                    if (ds['close'][pos] >= max(ds['close'][pos -period+1 :pos + 1])):
                        dh.at[ts, item.id] = 1
                    else:
                        dh.at[ts, item.id] = 0
                else:
                    dh.at[ts,item.id] = 0

    df['total'] = dh.apply(lambda x:x.sum(),axis=1)
    df['index_c'] = df['close']
    dh.to_csv('newhigher.csv')
    return True

if __name__ == '__main__':
    # print(ma(security_item='000002', start_date='2017-01-01', end_date='2017-12-31'))
    # print(ema(security_item='000002', start_date='20171101', end_date='20171201'))
    # print(ema(get_security_item('000001'), start='20171101', end='20171201'))
    #print(macd(security_item='000002', start_date='20170101', end_date='20171201'))
    newhighergenerator('2005-01-01')
