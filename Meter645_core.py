'''
    645模拟表程序
'''
import Comm, binascii, re, serial, time, datetime, configparser, traceback


def Electricity_meter_date_and_week_and_time(data):
    if data == '@GetDateWeek@':
        time1_str = datetime.datetime.now().strftime('%C%m%d%w')
        if len(time1_str) == 7:
            time1_str = time1_str[0:6] + '0' + time1_str[-1]
        return time1_str
    elif data == '@GetTime@':
        time2_str = datetime.datetime.now().strftime('%T').replace(':', '')
        return time2_str
    elif data == '@FreezeTime@':
        # time3_str = datetime.datetime.now().strftime('%M%H%d%m%y').replace(':', '')
        time3_str = datetime.datetime.now().strftime('%y%m%d0000')
        return time3_str
    else:
        print('Electricity_meter_date_and_week_and_time not found!')


def conctrlcode(code):
    if code == '11':
        recode = int(code, 16) + 128
        recode = hex(recode)[2:]
        return recode


def data_len(code):
    m = hex(int(code, 16) - 4)[2]
    if m == '0':
        return m
    if m == '1':
        pass
    if m == '6':
        return m


def strto0x(context):  # list
    context = [int(x, 16) for x in context]
    new_context = []
    while context:
        current_context = chr(context.pop())
        new_context.append(current_context)
    new_context.reverse()
    return new_context


def CS(list, b):
    sum = 0
    while list:
        sum = sum + ord(list.pop())
    sum = hex(sum & 0xff)[2:]
    if len(sum) == 1:
        sum = "0" + sum
    try:
        if sum == b.lower():
            pass
    except:
        if b is None:
            pass
        else:
            print('校验错误')
    return sum


def readdata(OI):
    conf_new = configparser.ConfigParser()
    conf_new.read('config.ini', encoding='utf-8')
    try:
        get = conf_new.get('MeterData645', OI)
        get = get.split(' ')
        text = [OI, get[0], get[1]]
        print("事件", text)
        data = (text[-1]).replace(',', '')
        name = text[-2]
        if data[0] == '@':
            data_time = Electricity_meter_date_and_week_and_time(data)
            print('数据标识及时间', name, datetime.datetime.now().strftime('%T'))
            return data_time, name
        print('数据标识及时间:', name, datetime.datetime.now().strftime('%T'))
        return data, name

    except:
        print('未知数据标识: ', OI)
        if OI[0].upper() == 'X' or OI.__len__() != 8:
            return None
        else:
            traceback.print_exc(file=open('bug.txt', 'a+'))
    return None


def plus33(message):
    newstr = ''
    if message is None:
        print('plus33 is none')
    else:
        if re.findall(',', message):
            message = message.split(',')
            lenth = len(message)
            i = 0
            while lenth:
                new_list = []
                lenth -= 1
                returnvalue = Comm.makelist(message[i])
                i += 1
                while returnvalue:
                    new_list.append(hex(int(returnvalue.pop(), 16) + 51)[2:])
                value_str = Comm.list2str(new_list)
                newstr = newstr + value_str
                return newstr
        else:
            message = Comm.makelist(message)
            lenth = len(message)
            new_list = []
            while lenth:
                lenth -= 1
                new_list.append(hex(int(message.pop(), 16) + 51)[2:])
            newstr = Comm.list2str(new_list)
            return newstr


def minus33(list):
    new_list = []
    while list:
        middle = hex(int(list.pop(), 16) - 51)[2:]
        if len(middle) == 1:
            middle = '0' + middle
        if middle == 'x1':
            middle = 'FF'
        new_list.append(middle)
    return new_list


def returnframe(add, reconctrlcode, L, D, N):
    text = '68' + add + '68' + reconctrlcode + L + D + N
    cs = CS(strto0x(Comm.makelist(text)), None)
    text = text + cs + '16'
    return text


def deal_receive(message):
    if message[8] == "13":
        text = "68 01 00 00 00 00 00 68 93 06 34 33 33 33 33 33 9D 16".replace(' ', '')
        return (text, '0', '0')
    while 1:
        if message[0] == '68':
            address = message[1:7]
            if address == ['aa', 'aa', 'aa', 'aa', 'aa', 'aa'] or address == ['99', '99', '99', '99', '99', '99']:
                # if address[0] == 'aa' or address[0] == '99':
                address = ['01', '00', '00', '00', '00', '00']
            break
        else:
            del message[0]
    reconctrlcode = conctrlcode(message[8])
    datasign = message[10:14]
    D = Comm.list2str(datasign)
    cs = CS(strto0x(message[0:-2]), message[-2])
    OI = Comm.list2str(minus33(datasign)).upper()
    a = readdata(OI)
    if not a:
        print('OI 无法解析: ', OI)
        returnstr = ''
        reconctrlcode = 'D100'
        L = ''
        D = ''
        text = returnframe(Comm.list2str(address), reconctrlcode, L, D, returnstr)
        if OI[0].upper() == 'X':
            return (text, '无法解析')
        else:
            return (text, '无法解析:', OI)
    else:
        # if re.match("0201FF00", OI):
        #     returnstr = "3232" + "3232" * 2;

        if re.match("0610", OI):
            TIME = Comm.list2str(message[15:20])
            print("time:", TIME, message[14])
            times = int(message[14], 16) - 33
            print("times:", times)
            returnstr = TIME + plus33(a[0]) * times
        else:
            returnstr = plus33(a[0])  # Date!!!!
        L = hex(4 + len(Comm.makelist(returnstr)))[2:].zfill(2)
        text = returnframe(Comm.list2str(address), reconctrlcode, L, D, returnstr)
        print('Sending:', text)
    return (text, OI + " " + a[1], a[0])
