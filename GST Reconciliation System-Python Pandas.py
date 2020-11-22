            ****** GST Tax reconciliation system using python ,pandas and django *****
            
 /* THE BELOW CODE IS TO reconcile multiple tax features by performing calculations and there by identifying mismatches which will be reported in the form of deviations in excel file sent to respective customers to their mail address*/

-- Used Python pandas , the code has calculations for multiple tax features which reconciles already paid tax to  the Government against company/organization tax paid numbers .
-- The deviations are identified and reported in the excel sent through the mail to the recepients
-- Kindly let me know if any clarification - mail me - prabhuram87@gmail.com

Future developments:
--------------------
-- For now , this is done offline , but in future 
Django is used as front end where user uploads the excel file of the tax paid which will reconcile against the government tax paid for the particular organization and provide the deviations to the customers.

from django.shortcuts import render, HttpResponse
import pandas as pd
import matplotlib.pyplot
import tempfile
import os
import csv
import string
import numpy as np
from openpyxl import load_workbook
from datetime import datetime
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from openpyxl.chart import BarChart, Series, Reference

# Create your views here.
def home(request):
    msg1="Instructions:  Please upload both the files and then click on Reconcile"


    if request.method == 'POST' and request.FILES['myfile'] and request.FILES['myfile1']:
        excel = request.FILES['myfile']
        excl = request.FILES['myfile1']
        df1 = pd.read_csv(excel, error_bad_lines=False, encoding='utf-8')
        df2 = pd.read_csv(excl, error_bad_lines=False, encoding='utf-8')

        df1.columns = ['gstin', 'invoice_date', 'customer_name', 'invoiceno', 'ctinno', 'taxablevalue', 'cgst', 'sgst',
                       'igst']
        df2.columns = ['gstin','period','ctinno','customer_name','counter_filing_status','invoiceno','invoice_value',
                       'invoice_date','placeofsupply','invoicetype'
                       ,'reversecharge','num','rate','taxablevalue','igst','cgst','sgst','cess']

        df1['invoice_date'] = pd.to_datetime(df1['invoice_date'])
        df2['invoice_date'] = pd.to_datetime(df2['invoice_date'])

        df1.loc[df1['invoice_date'].between('2017-04-01', '2018-03-31', inclusive=True), 'FY'] = '2017-18'
        df1.loc[df1['invoice_date'].between('2018-04-01', '2019-03-31', inclusive=True), 'FY'] = '2018-19'
        df1.loc[df1['invoice_date'].between('2019-04-01', '2020-03-31', inclusive=True), 'FY'] = '2019-20'
        df1.loc[df1['invoice_date'].between('2020-04-01', '2021-03-31', inclusive=True), 'FY'] = '2020-21'

        df2.loc[df2['invoice_date'].between('2017-04-01', '2018-03-31', inclusive=True), 'FY'] = '2017-18'
        df2.loc[df2['invoice_date'].between('2018-04-01', '2019-03-31', inclusive=True), 'FY'] = '2018-19'
        df2.loc[df2['invoice_date'].between('2019-04-01', '2020-03-31', inclusive=True), 'FY'] = '2019-20'
        df2.loc[df2['invoice_date'].between('2020-04-01', '2021-03-31', inclusive=True), 'FY'] = '2020-21'

        df1.fillna(0, inplace=True)
        df2.fillna(0, inplace=True)

        df1.taxablevalue = df1.taxablevalue.round(decimals=0).astype('int64')
        df2.taxablevalue = df2.taxablevalue.round(decimals=0).astype('int64')

        df1["length"] = (df1['ctinno'].str.len() == 15)
        df2["length"] = (df2['ctinno'].str.len() == 15)

        df1['totaltax'] = df1['cgst'] + df1['sgst'] + df1['igst']
        df2['totaltax'] = df2['cgst'] + df2['sgst'] + df2['igst']

        df1["Concat"]= df1["ctinno"].map(str)+df1["invoiceno"].map(str)+df1["FY"].map(str)+df1["taxablevalue"].map(str)+df1["totaltax"].map(str)
        df2["Concat"]= df2["ctinno"].map(str)+df2["invoiceno"].map(str)+df2["FY"].map(str)+df2["taxablevalue"].map(str)+df2["totaltax"].map(str)+df2["rate"].map(str)

        df1["dup_remove"] = df1.groupby(['Concat']).cumcount()+1
        df2["dup_remove"] = df2.groupby(['Concat']).cumcount()+1

        df1.loc[(df1['dup_remove']>1) ,'Dup_Remarks'] = 'Duplicate_Invoice'
        df2.loc[(df2['dup_remove']>1) ,'Dup_Remarks'] = 'Duplicate_Invoice'

        df1.loc[(df1['dup_remove']>1) ,'totaltax'] = 0
        df2.loc[(df2['dup_remove']>1) ,'totaltax'] = 0

        df1.loc[(df1['totaltax']<0) ,'totaltax'] = 0
        df2.loc[(df2['totaltax']<0) ,'totaltax'] = 0

        df1.loc[(df1['invoiceno']==0) ,'totaltax'] = 0
        df2.loc[(df2['invoiceno']==0) ,'totaltax'] = 0

        df1.totaltax = df1.totaltax.round(decimals=0).astype('int64')
        df2.totaltax = df2.totaltax.round(decimals=0).astype('int64')

        df1["ConcatColumn"] = df1["ctinno"].map(str) + df1["invoiceno"].map(str)
        df2["ConcatColumn"] = df2["ctinno"].map(str) + df2["invoiceno"].map(str)

        df1["ConcatColumn1"] = df1.groupby(['ConcatColumn'])['totaltax'].transform('sum')
        df2["ConcatColumn1"] = df2.groupby(['ConcatColumn'])['totaltax'].transform('sum')

        df1["dup_number"] = df1.groupby(['ConcatColumn']).cumcount() + 1
        df2["dup_number"] = df2.groupby(['ConcatColumn']).cumcount() + 1

        df1["ConcatColumn_dup"] = df1["dup_number"].map(str) + df1["ConcatColumn"].map(str)
        df2["ConcatColumn_dup"] = df2["dup_number"].map(str) + df2["ConcatColumn"].map(str)

        New_one = pd.merge(left=df1, right=df2[['ConcatColumn_dup', 'ConcatColumn1']], left_on='ConcatColumn_dup',
                           right_on='ConcatColumn_dup', how='left')
        New_two = pd.merge(left=df2, right=df1[['ConcatColumn_dup', 'ConcatColumn1']], left_on='ConcatColumn_dup',
                           right_on='ConcatColumn_dup', how='left')

        New_one['Flag'] = False
        New_one.loc[New_one.ConcatColumn_dup.isin(
            New_two.drop_duplicates(subset=['ConcatColumn_dup']).ConcatColumn_dup.values), 'Flag'] = True

        New_two['Flag'] = False
        New_two.loc[New_two.ConcatColumn_dup.isin(
            New_one.drop_duplicates(subset=['ConcatColumn_dup']).ConcatColumn_dup.values), 'Flag'] = True

        New_one["ConcatColumn1a"] = New_one.groupby(['ConcatColumn'])['ConcatColumn1_y'].transform('sum')
        New_two["ConcatColumn1a"] = New_two.groupby(['ConcatColumn'])['ConcatColumn1_y'].transform('sum')

        New_one.loc[New_one['ConcatColumn1_y'].isnull(), 'ConcatColumn1_y'] = New_one['ConcatColumn1a']
        New_two.loc[New_two['ConcatColumn1_y'].isnull(), 'ConcatColumn1_y'] = New_two['ConcatColumn1a']

        New_one['Diff1'] = New_one['ConcatColumn1_x'] - New_one['ConcatColumn1_y']
        New_two['Diff1'] = New_two['ConcatColumn1_x'] - New_two['ConcatColumn1_y']

        New_one['Remarks1'] = False
        New_one.loc[New_one['Diff1'].between(-10.00, 10.00, inclusive=True) & (New_one['dup_remove'] == 1) & (
                    New_one['ConcatColumn1_y'] != 0), 'Remarks1'] = True
        New_two['Remarks1'] = False
        New_two.loc[New_two['Diff1'].between(-10.00, 10.00, inclusive=True) & (New_two['dup_remove'] == 1) & (
                    New_two['ConcatColumn1_y'] != 0), 'Remarks1'] = True
##Level 1 comlpeted ##

        ###### Stage 2 validation - Modified Invoice

        New_one['invoiceno_New'] = New_one['invoiceno'].replace(
            [" ", 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
             'u', 'v', 'w', 'x', 'y', 'z',
             'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
             'V', 'W', 'X', 'Y', 'Z',
             '2017-18', '2017-2018', '2018-19', '2018-2019', '/1718', '/1819', '/17-18', '17-18/', '17-18',
             '18-19', '/17 ', '/18 ', '/2017', '/2018', '/2019', '-', '/', '&', " "], '', regex=True)
        New_one['invoiceno_New1'] = New_one.invoiceno_New.str.lstrip("0")
        New_one["invoiceno_New1"].fillna(New_one.invoiceno_New, inplace=True)
        New_two['invoiceno_New'] = New_two['invoiceno'].replace(
            [" ", 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
             'u', 'v', 'w', 'x', 'y', 'z',
             'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
             'V', 'W', 'X', 'Y', 'Z',
             '2017-18', '2017-2018', '2018-19', '2018-2019', '/1718', '/1819', '/17-18', '17-18/', '17-18',
             '18-19', '/17 ', '/18 ', '/2017', '/2018', '/2019', '-', '/', '&', " "], '', regex=True)
        New_two['invoiceno_New1'] = New_two.invoiceno_New.str.lstrip("0")
        New_two["invoiceno_New1"].fillna(New_two.invoiceno_New, inplace=True)

        New_one["Concat1"] = New_one["ctinno"].map(str) + New_one["invoiceno_New1"].map(str) + New_one["FY"].map(str) + \
                             New_one["taxablevalue"].map(str) + New_one["totaltax"].map(str)
        New_two["Concat1"] = New_two["ctinno"].map(str) + New_two["invoiceno_New1"].map(str) + New_two["FY"].map(str) + \
                             New_two["taxablevalue"].map(str) + New_two["totaltax"].map(str) + New_two["rate"].map(str)

        New_one["dup_remove1"] = New_one.groupby(['Concat1']).cumcount() + 1
        New_two["dup_remove1"] = New_two.groupby(['Concat1']).cumcount() + 1

        New_one.loc[(New_one['dup_remove1'] > 1), 'Dup_Remarks'] = 'Duplicate_Invoice'
        New_two.loc[(New_two['dup_remove1'] > 1), 'Dup_Remarks'] = 'Duplicate_Invoice'

        New_one.loc[(New_one['dup_remove1'] > 1), 'totaltax'] = 0
        New_two.loc[(New_two['dup_remove1'] > 1), 'totaltax'] = 0

        New_one["ConcatColumn2"] = New_one["ctinno"].map(str) + New_one["invoiceno_New1"].map(str) + New_one["FY"].map(
            str)
        New_two["ConcatColumn2"] = New_two["ctinno"].map(str) + New_two["invoiceno_New1"].map(str) + New_one["FY"].map(
            str)

        New_one["ConcatColumn2a"] = New_one.groupby(['ConcatColumn2'])['totaltax'].transform('sum')
        New_two["ConcatColumn2a"] = New_two.groupby(['ConcatColumn2'])['totaltax'].transform('sum')

        New_one["dup_number2"] = New_one.groupby(['ConcatColumn2']).cumcount() + 1
        New_two["dup_number2"] = New_two.groupby(['ConcatColumn2']).cumcount() + 1

        New_one["ConcatColumn_dup2"] = New_one["dup_number2"].map(str) + New_one["ConcatColumn2"].map(str)
        New_two["ConcatColumn_dup2"] = New_two["dup_number2"].map(str) + New_two["ConcatColumn2"].map(str)

        New_3 = pd.merge(left=New_one, right=New_two[['ConcatColumn_dup2', 'ConcatColumn2a']],
                         left_on='ConcatColumn_dup2', right_on='ConcatColumn_dup2', how='left')
        New_4 = pd.merge(left=New_two, right=New_one[['ConcatColumn_dup2', 'ConcatColumn2a']],
                         left_on='ConcatColumn_dup2', right_on='ConcatColumn_dup2', how='left')

        New_3['Flag2'] = False
        New_3.loc[New_3.ConcatColumn_dup2.isin(
            New_4.drop_duplicates(subset=['ConcatColumn_dup2']).ConcatColumn_dup2.values), 'Flag2'] = True

        New_4['Flag2'] = False
        New_4.loc[New_4.ConcatColumn_dup2.isin(
            New_3.drop_duplicates(subset=['ConcatColumn_dup2']).ConcatColumn_dup2.values), 'Flag2'] = True

        New_3["ConcatColumn2a1"] = New_3.groupby(['ConcatColumn2'])['ConcatColumn2a_y'].transform('sum')
        New_4["ConcatColumn2a1"] = New_4.groupby(['ConcatColumn2'])['ConcatColumn2a_y'].transform('sum')

        New_3.loc[New_3['ConcatColumn2a_y'].isnull(), 'ConcatColumn2a_y'] = New_3['ConcatColumn2a1']
        New_4.loc[New_4['ConcatColumn2a_y'].isnull(), 'ConcatColumn2a_y'] = New_4['ConcatColumn2a1']

        New_3['Diff2'] = New_3['ConcatColumn2a_x'] - New_3['ConcatColumn2a_y']
        New_4['Diff2'] = New_4['ConcatColumn2a_x'] - New_4['ConcatColumn2a_y']

        New_3['Remarks2'] = False
        New_3.loc[New_3['Diff2'].between(-10.00, 10.00, inclusive=True) & (New_3['dup_remove1'] == 1) & (
                    New_3['ConcatColumn2a_y'] != 0), 'Remarks2'] = True
        New_4['Remarks2'] = False
        New_4.loc[New_4['Diff2'].between(-10.00, 10.00, inclusive=True) & (New_4['dup_remove1'] == 1) & (
                    New_4['ConcatColumn2a_y'] != 0), 'Remarks2'] = True
        ###### Stage 3 Validation - taxablevalue

        New_3["ConcatColumn3"] = New_3["ctinno"].map(str) + New_3["taxablevalue"].map(str) + New_3["FY"].map(str)
        New_4["ConcatColumn3"] = New_4["ctinno"].map(str) + New_4["taxablevalue"].map(str) + New_4["FY"].map(str)

        New_3.loc[(New_3['Remarks1'] == False) & (New_3['Remarks2'] == False), 'ConcatColumn3a'] = \
        New_3.groupby(['ConcatColumn3'])['totaltax'].transform('sum')
        New_4.loc[(New_4['Remarks1'] == False) & (New_4['Remarks2'] == False), 'ConcatColumn3a'] = \
        New_4.groupby(['ConcatColumn3'])['totaltax'].transform('sum')

        New_3["dup_number3"] = New_3.groupby(['ConcatColumn3']).cumcount() + 1
        New_4["dup_number3"] = New_4.groupby(['ConcatColumn3']).cumcount() + 1

        New_3["ConcatColumn_dup3"] = New_3["dup_number3"].map(str) + New_3["ConcatColumn3"].map(str)
        New_4["ConcatColumn_dup3"] = New_4["dup_number3"].map(str) + New_4["ConcatColumn3"].map(str)

        New_5 = pd.merge(left=New_3, right=New_4[['ConcatColumn_dup3', 'ConcatColumn3a']], left_on='ConcatColumn_dup3',
                         right_on='ConcatColumn_dup3', how='left')
        New_6 = pd.merge(left=New_4, right=New_3[['ConcatColumn_dup3', 'ConcatColumn3a']], left_on='ConcatColumn_dup3',
                         right_on='ConcatColumn_dup3', how='left')

        New_5['Flag3'] = False
        New_5.loc[New_5.ConcatColumn_dup3.isin(
            New_6.drop_duplicates(subset=['ConcatColumn_dup3']).ConcatColumn_dup3.values), 'Flag3'] = True

        New_6['Flag3'] = False
        New_6.loc[New_6.ConcatColumn_dup3.isin(
            New_5.drop_duplicates(subset=['ConcatColumn_dup3']).ConcatColumn_dup3.values), 'Flag3'] = True

        New_5["ConcatColumn3a1"] = New_5.groupby(['ConcatColumn3'])['ConcatColumn3a_y'].transform('mean')
        New_6["ConcatColumn3a1"] = New_6.groupby(['ConcatColumn3'])['ConcatColumn3a_y'].transform('mean')

        New_5.loc[New_5['ConcatColumn3a_y'].isnull(), 'ConcatColumn3a_y'] = New_5['ConcatColumn3a1']
        New_6.loc[New_6['ConcatColumn3a_y'].isnull(), 'ConcatColumn3a_y'] = New_6['ConcatColumn3a1']

        New_5['Diff3'] = New_5['ConcatColumn3a_x'] - New_5['ConcatColumn3a_y']
        New_6['Diff3'] = New_6['ConcatColumn3a_x'] - New_6['ConcatColumn3a_y']

        New_5['Remarks3'] = False
        New_5.loc[
            New_5['Diff3'].between(-10.00, 10.00, inclusive=True) & (New_5['ConcatColumn3a_y'] != 0), 'Remarks3'] = True
        New_6['Remarks3'] = False
        New_6.loc[
            New_6['Diff3'].between(-10.00, 10.00, inclusive=True) & (New_6['ConcatColumn3a_y'] != 0), 'Remarks3'] = True
        ###### Stage 4 Validation - GST Only

        New_5["ConcatColumn4"] = New_5["ctinno"].map(str) + New_5["FY"].map(str)
        New_6["ConcatColumn4"] = New_6["ctinno"].map(str) + New_6["FY"].map(str)

        New_5["dup_number4"] = New_5.groupby(['ConcatColumn4']).cumcount() + 1
        New_6["dup_number4"] = New_6.groupby(['ConcatColumn4']).cumcount() + 1

        New_5["ConcatColumn_dup4"] = New_5["dup_number4"].map(str) + New_5["ConcatColumn4"].map(str)
        New_6["ConcatColumn_dup4"] = New_6["dup_number4"].map(str) + New_6["ConcatColumn4"].map(str)

        New_5["ConcatColumn4a"] = New_5.groupby(['ConcatColumn4'])['totaltax'].transform('sum')
        New_6["ConcatColumn4a"] = New_6.groupby(['ConcatColumn4'])['totaltax'].transform('sum')

        New_7 = pd.merge(left=New_5, right=New_6[['ConcatColumn_dup4', 'ConcatColumn4a']], left_on='ConcatColumn_dup4',
                         right_on='ConcatColumn_dup4', how='left')
        New_8 = pd.merge(left=New_6, right=New_5[['ConcatColumn_dup4', 'ConcatColumn4a']], left_on='ConcatColumn_dup4',
                         right_on='ConcatColumn_dup4', how='left')

        New_7['Flag4'] = False
        New_7.loc[New_7.ConcatColumn_dup4.isin(
            New_8.drop_duplicates(subset=['ConcatColumn_dup4']).ConcatColumn_dup4.values), 'Flag4'] = True

        New_8['Flag4'] = False
        New_8.loc[New_8.ConcatColumn_dup4.isin(
            New_7.drop_duplicates(subset=['ConcatColumn_dup4']).ConcatColumn_dup4.values), 'Flag4'] = True

        New_7["ConcatColumn4a1"] = New_7.groupby(['ctinno'])['ConcatColumn4a_y'].transform('mean')
        New_8["ConcatColumn4a1"] = New_8.groupby(['ctinno'])['ConcatColumn4a_y'].transform('mean')

        New_7.loc[New_7['ConcatColumn4a_y'].isnull(), 'ConcatColumn4a_y'] = New_7['ConcatColumn4a1']
        New_8.loc[New_8['ConcatColumn4a_y'].isnull(), 'ConcatColumn4a_y'] = New_8['ConcatColumn4a1']

        New_7['Diff4'] = New_7['ConcatColumn4a_x'] - New_7['ConcatColumn4a_y']
        New_8['Diff4'] = New_8['ConcatColumn4a_x'] - New_8['ConcatColumn4a_y']

        New_7['Remarks4'] = False
        New_7.loc[
            New_7['Diff4'].between(-10.00, 10.00, inclusive=True) & (New_7['ConcatColumn4a_y'] != 0), 'Remarks4'] = True
        New_8['Remarks4'] = False
        New_8.loc[
            New_8['Diff4'].between(-10.00, 10.00, inclusive=True) & (New_8['ConcatColumn4a_y'] != 0), 'Remarks4'] = True

        ###### Stage 5 Validation - GST+ConcatColumn1_x

        New_7["ConcatColumn5"] = New_7["ctinno"].map(str) + New_7["ConcatColumn1_x"].map(str) + New_7["FY"].map(str)
        New_8["ConcatColumn5"] = New_8["ctinno"].map(str) + New_8["ConcatColumn1_x"].map(str) + New_8["FY"].map(str)

        New_7.loc[(New_7['Remarks1'] == False) & (New_7['Remarks2'] == False) & (
                    New_7['Remarks3'] == False), 'ConcatColumn5a'] = New_7.groupby(['ConcatColumn5'])[
            'totaltax'].transform('sum')
        New_8.loc[(New_8['Remarks1'] == False) & (New_8['Remarks2'] == False) & (
                    New_8['Remarks3'] == False), 'ConcatColumn5a'] = New_8.groupby(['ConcatColumn5'])[
            'totaltax'].transform('sum')

        New_7["dup_number5"] = New_7.groupby(['ConcatColumn5']).cumcount() + 1
        New_8["dup_number5"] = New_8.groupby(['ConcatColumn5']).cumcount() + 1

        New_7["ConcatColumn_dup5"] = New_7["dup_number5"].map(str) + New_7["ConcatColumn5"].map(str)
        New_8["ConcatColumn_dup5"] = New_8["dup_number5"].map(str) + New_8["ConcatColumn5"].map(str)

        New_9 = pd.merge(left=New_7, right=New_8[['ConcatColumn_dup5', 'ConcatColumn5a']], left_on='ConcatColumn_dup5',
                         right_on='ConcatColumn_dup5', how='left')
        New_10 = pd.merge(left=New_8, right=New_7[['ConcatColumn_dup5', 'ConcatColumn5a']], left_on='ConcatColumn_dup5',
                          right_on='ConcatColumn_dup5', how='left')

        New_9["Flag5"] = (New_9['ConcatColumn5a_y'] > 0)
        New_10["Flag5"] = (New_10['ConcatColumn5a_y'] > 0)

        New_9["ConcatColumn5a1"] = New_9.groupby(['ConcatColumn5'])['ConcatColumn5a_y'].transform('mean')
        New_10["ConcatColumn5a1"] = New_10.groupby(['ConcatColumn5'])['ConcatColumn5a_y'].transform('mean')

        New_9.loc[New_9['ConcatColumn5a_y'].isnull(), 'ConcatColumn5a_y'] = New_9['ConcatColumn5a1']
        New_10.loc[New_10['ConcatColumn5a_y'].isnull(), 'ConcatColumn5a_y'] = New_10['ConcatColumn5a1']

        New_9['Diff5'] = New_9['ConcatColumn5a_x'] - New_9['ConcatColumn5a_y']
        New_10['Diff5'] = New_10['ConcatColumn5a_x'] - New_10['ConcatColumn5a_y']

        New_9['Remarks5'] = False
        New_9.loc[
            New_9['Diff5'].between(-10.00, 10.00, inclusive=True) & (New_9['ConcatColumn5a_y'] != 0), 'Remarks5'] = True
        New_10['Remarks5'] = False
        New_10.loc[New_10['Diff5'].between(-10.00, 10.00, inclusive=True) & (
                    New_10['ConcatColumn5a_y'] != 0), 'Remarks5'] = True

        ############******************************

        New_9['Datasource'] = 'Invoice'
        New_10['Datasource'] = 'Portal'

        ##### Invoice Remarks Validation

        New_9.loc[(New_9['length'] == False), 'Final_Remarks'] = 'GSTIN_Number_Error'

        New_9.loc[(New_9['length'] == True) & (
                    New_9['Dup_Remarks'] == 'Duplicate_Invoice'), 'Final_Remarks'] = 'Duplicate_Invoice'

        New_9.loc[(New_9['length'] == True) & (New_9['Dup_Remarks'].isnull()) & (
                    New_9['totaltax'] < 0), 'Final_Remarks'] = 'Total_Tax_is_Negative'

        New_9.loc[(New_9['length'] == True) & (New_9['Dup_Remarks'].isnull()) & (
                    New_9['invoiceno'] == 0), 'Final_Remarks'] = 'Invoice_number_Wrong'

        New_9.loc[(New_9['length'] == True) & (New_9['Dup_Remarks'].isnull()) & (
                    New_9['totaltax'] == 0), 'Final_Remarks'] = 'Total_Tax_Value_is_Zero'

        New_9.loc[
            (New_9['Remarks1'] == True) & (New_9['Final_Remarks'].isnull()), 'Final_Remarks'] = '1_Completely_Matched'

        New_9.loc[(New_9['Remarks1'] == False) & (New_9['Remarks2'] == True) & (
            New_9['Final_Remarks'].isnull()), 'Final_Remarks'] = '2_Conditionally_Matched'

        New_9.loc[(New_9['Remarks1'] == False) & (New_9['Remarks2'] == False) & (New_9['Remarks3'] == True) & (
            New_9['Final_Remarks'].isnull()), 'Final_Remarks'] = '3_Taxablevalue_Tax_Matched'

        New_9.loc[(New_9['Remarks1'] == False) & (New_9['Remarks2'] == False) & (New_9['Remarks3'] == False) & (
                    New_9['Remarks5'] == True) & (
                      New_9['Final_Remarks'].isnull()), 'Final_Remarks'] = '4_GSTIN+TotalTaxSum_Tax_Matched'

        New_9.loc[(New_9['Remarks1'] == False) & (New_9['Remarks2'] == False) & (New_9['Remarks3'] == False) & (
                    New_9['Remarks5'] == False) & (New_9['Remarks4'] == True) & (
                      New_9['Final_Remarks'].isnull()), 'Final_Remarks'] = '5_GSTIN_Only_Tax_Matched'

        New_9.loc[(New_9['Final_Remarks'].isnull()) & (New_9['ConcatColumn1_y'] != 0) & (
                    New_9['Diff1'] < 0), 'Final_Remarks'] = 'Excess_Tax_in_Portal'
        New_9.loc[(New_9['Final_Remarks'].isnull()) & (New_9['ConcatColumn1_y'] != 0) & (
                    New_9['Diff1'] > 0), 'Final_Remarks'] = 'Excess_Tax_in_Invoice'

        New_9.loc[(New_9['Final_Remarks'].isnull()) & (New_9['ConcatColumn2a_y'] != 0) & (
                    New_9['Diff2'] < 0), 'Final_Remarks'] = 'Excess_Tax_in_Portal'
        New_9.loc[(New_9['Final_Remarks'].isnull()) & (New_9['ConcatColumn2a_y'] != 0) & (
                    New_9['Diff2'] > 0), 'Final_Remarks'] = 'Excess_Tax_in_Invoice'

        New_9.loc[(New_9['Final_Remarks'].isnull()), 'Final_Remarks'] = 'Available_in_Purchse_register_Not_in_Portal'

        ##### Portal Remarks Validation

        New_10.loc[(New_10['length'] == False), 'Final_Remarks'] = 'GSTIN_Number_Error'

        New_10.loc[(New_10['length'] == True) & (
                    New_10['Dup_Remarks'] == 'Duplicate_Invoice'), 'Final_Remarks'] = 'Duplicate_Invoice'

        New_10.loc[(New_10['length'] == True) & (New_10['Dup_Remarks'].isnull()) & (
                    New_10['totaltax'] < 0), 'Final_Remarks'] = 'Total_Tax_is_Negative'

        New_10.loc[(New_10['length'] == True) & (New_10['Dup_Remarks'].isnull()) & (
                    New_10['invoiceno'] == 0), 'Final_Remarks'] = 'Invoice_number_Wrong'

        New_10.loc[(New_10['length'] == True) & (New_10['Dup_Remarks'].isnull()) & (
                    New_10['totaltax'] == 0), 'Final_Remarks'] = 'Total_Tax_Value_is_Zero'

        New_10.loc[
            (New_10['Remarks1'] == True) & (New_10['Final_Remarks'].isnull()), 'Final_Remarks'] = '1_Completely_Matched'

        New_10.loc[(New_10['Remarks1'] == False) & (New_10['Remarks2'] == True) & (
            New_10['Final_Remarks'].isnull()), 'Final_Remarks'] = '2_Conditionally_Matched'

        New_10.loc[(New_10['Remarks1'] == False) & (New_10['Remarks2'] == False) & (New_10['Remarks3'] == True) & (
            New_10['Final_Remarks'].isnull()), 'Final_Remarks'] = '3_Taxablevalue_Tax_Matched'

        New_10.loc[(New_10['Remarks1'] == False) & (New_10['Remarks2'] == False) & (New_10['Remarks3'] == False) & (
                    New_10['Remarks5'] == True) & (
                       New_10['Final_Remarks'].isnull()), 'Final_Remarks'] = '4_GSTIN+TotalTaxSum_Tax_Matched'

        New_10.loc[(New_10['Remarks1'] == False) & (New_10['Remarks2'] == False) & (New_10['Remarks3'] == False) & (
                    New_10['Remarks5'] == False) & (New_10['Remarks4'] == True) & (
                       New_10['Final_Remarks'].isnull()), 'Final_Remarks'] = '5_GSTIN_Only_Tax_Matched'

        New_10.loc[(New_10['Final_Remarks'].isnull()) & (New_10['ConcatColumn1_y'] != 0) & (
                    New_10['Diff1'] > 0), 'Final_Remarks'] = 'Excess_Tax_in_Portal'
        New_10.loc[(New_10['Final_Remarks'].isnull()) & (New_10['ConcatColumn1_y'] != 0) & (
                    New_10['Diff1'] < 0), 'Final_Remarks'] = 'Excess_Tax_in_Invoice'

        New_10.loc[(New_10['Final_Remarks'].isnull()) & (New_10['ConcatColumn2a_y'] != 0) & (
                    New_10['Diff2'] > 0), 'Final_Remarks'] = 'Excess_Tax_in_Portal'
        New_10.loc[(New_10['Final_Remarks'].isnull()) & (New_10['ConcatColumn2a_y'] != 0) & (
                    New_10['Diff2'] < 0), 'Final_Remarks'] = 'Excess_Tax_in_Invoice'

        New_10.loc[(New_10['Final_Remarks'].isnull()), 'Final_Remarks'] = 'Available_in_Portal_Not_In_Purchse_register'

        invoice_output = New_9[
            ["ctinno", "FY", "gstin", "invoice_date", "invoiceno", "invoiceno_New1", "taxablevalue", "totaltax",
             "Datasource", "Final_Remarks", "cgst", "sgst", "igst", ]]
        portal_output = New_10[
            ["ctinno", "FY", "gstin", "invoice_date", "invoiceno", "invoiceno_New1", "taxablevalue", "totaltax",
             "Datasource", "Final_Remarks", "cgst", "sgst", "igst"]]
        consol_output = portal_output.append(invoice_output)


        df11 = pd.pivot_table(consol_output, index=['Final_Remarks', 'ctinno', 'invoiceno'], columns=['Datasource'],
                              values=['totaltax'],
                              aggfunc='sum', fill_value=0, margins=True, margins_name='GrandTotal')
        df11.drop(columns='GrandTotal', axis=1, level=1, inplace=True)

        df12 = pd.pivot_table(consol_output, index=['Final_Remarks', 'FY', ], columns=['Datasource'],
                              values=['totaltax'],
                              aggfunc='sum', fill_value=0, margins=True, margins_name='GrandTotal')
        df12.drop(columns='GrandTotal', axis=1, level=1, inplace=True)

        #df12.plot.bar(rot=0, subplots=True)





        with tempfile.TemporaryDirectory() as tmpdirname:
            path = os.path.join(tmpdirname, 'sample.xlsx')
            print('created temporary directory', tmpdirname)
            with pd.ExcelWriter(path) as writer:
                consol_output.to_excel(writer, sheet_name='Main_Output')
                df11.to_excel(writer, sheet_name='Aggregation')
                df12.to_excel(writer, sheet_name='Summary')

                


            fromaddr = "ABC@gmail.com"
            toaddr = "ABC@gmail.com"

            # instance of MIMEMultipart
            msg = MIMEMultipart()

            # storing the senders email address
            msg['From'] = fromaddr

            # storing the receivers email address
            msg['To'] = toaddr

            # storing the subject
            msg['Subject'] = "Hello XYZ"

            # string to store the body of the mail
            body = "Reconciliation Report"

            # attach the body with the msg instance
            msg.attach(MIMEText(body, 'plain'))

            # open the file to be sent
            filename = "sample.xlsx"
            attachment = open(path, "rb")


            # instance of MIMEBase and named as p
            p = MIMEBase('application', 'octet-stream')

            # To change the payload into encoded form
            p.set_payload((attachment).read())

            # encode into base64
            encoders.encode_base64(p)

            p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

            # attach the instance 'p' to instance 'msg'
            msg.attach(p)
            attachment.close()

            # creates SMTP session
            s = smtplib.SMTP('smtp.gmail.com', 587)

            # start TLS for security
            s.starttls()

            # Authentication
            s.login(fromaddr, "abc@123")

            # Converts the Multipart msg into a string
            text = msg.as_string()

            # sending the mail
            s.sendmail(fromaddr, toaddr, text)

            s.quit()
            msg1="Mail Sent Successfully"




    return render(request, 'excel_reader/home.html', {'Message':msg1})