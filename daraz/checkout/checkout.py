from django.shortcuts import render, redirect
import random
from djangoProject6.settings import EMAIL_HOST_USER
from datetime import datetime
from django.db import connection
from django.core.mail import send_mail


def getPrice(product):
    try:
        cur = connection.cursor()
        cur.execute("select PRICE from PRODUCTS where PRODUCT_ID = %s",[product])
        result = cur.fetchone()
        price = result[0]
    except:
        print('not found')
        price = 0
    return price

def makeorder(request, peopleid, orderdate,pay_status,method):
    try:
        cart = request.session.get('cart')
    except:
        print('cart is empty')
        return redirect('place_your_order')
    cartkeys = list(cart.keys())
    name = request.session['name']
    email  = request.session['email']
    items = get_items(request)
    msg = 'Hello, ' + name + '\nYour Order has Been Placed SuccessFully.\n' + 'We will reach you to reconfirm very soon!\n' + 'You Have ' + str(
        request.session['pack']) + ' packages in process to recieve' + '\nYour orders: \n' + str(
        items) + '\nTotal cost: BDT ' + str(f"{request.session['total']+65 * request.session['pack']:,}")+ '\n'
            #+str(request.session['total'] + 65 * request.session['pack'])
    sub = 'Order Placed'
    try:
        cur = connection.cursor()
        i =0
        # paymentid = random.randrange(start=320983092,step=1)
        for id in cartkeys:
            qty = cart[id]
            producid = cartkeys[i]
            i+=1
            id = int(id)
            # orderid = random.randrange(start=id, step=1)
            # shipmentid = random.randrange(start=orderid, step=1)
            cost = qty*getPrice(id)
            try:
                sqlonOrder = "INSERT INTO ORDERS(ORDER_ID, CUSTOMER_ID, ORDER_DATE, AMOUNT, QUANTITY, PAYMENT_STATUS) VALUES (ORDERID.nextval,%s,%s,%s,%s,%s)"

                cur.execute(sqlonOrder, [peopleid, orderdate, cost, qty, pay_status])
                connection.commit()
                push_on_product_orders(producid)
                push_on_payment('True', method)
                try:
                    sendMail(email,sub,msg)
                except:
                    print('msg sending failed')
                    return redirect('order_place')
                # make_shipment(request, orderdate, orderid)
            except:
                print('this order is failed!')


            print('this order is successful!')
        cur.close()
    except:
        print('order failed!')
        return redirect('cart')


def push_on_product_orders(product):

    # print(cart)
    try:
        cur = connection.cursor()
        product = int(product)
        # print(qty,end=' ')
        cur.execute("INSERT INTO PRODUCT_ORDERS(ORDER_ID, PRODUCT_ID) VALUES (ORDERID.currval,%s)",
                    [product])
        connection.commit()
        print('success on pro_order')
    except:
        return redirect('order_place')



        # except:
        #     print('failed to push in product_orders table')
    # print('pushed succesfully on product_orders')
    cur.close()


def verify_pin(request):

    try:
        email = request.session['email']
    except:
        return redirect('login')
    try:
        cart = request.session.get('cart')
        print(cart)
        if len(cart.keys()) == 0:

            return redirect('homepage')
    except:
        return redirect('hompage')


    if request.method ==  'POST':
        pinfromuser = request.POST.get('pin')
        acc = request.session.get('phone')
        verified = False
        try:
            cur = Initiate_Cursor()
            cur.execute("select pin from BKASH where ACCNO = %s",[acc])
            result = cur.fetchone()
            pin = result[0]
            print(pin)
            if pin == int(pinfromuser):
                print('verified!')
                verified = True
            else:

                print('pin not mathced')
                return redirect('bkash')
        except:
            print('could not find the pin!')
            return redirect('bkash')
        if verified:

            peopleid = get_customer_id(email)
            items = get_items(request)
            # count = request.session['qty']
            orderdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(orderdate)
            '''Pushing  Orders in order Table'''
            items = str(items)
            print("products:" + items)
            method = 'bkash'
            '''Now put them on Product_Orders Table'''
            makeorder(request, peopleid, orderdate, 'True',method)
            print('order successful!')

            '''sending a mail to customer..'''
            print('sending email..')
            name = request.session['name']
            msg = 'Hello, ' + name + '\nYour Order has Been Placed SuccessFully.\n' + 'We will reach you to reconfirm very soon!\n' + 'You Have ' + str(
                request.session['pack']) +' packages in process to recieve' +'\nYour orders: \n' + str(
                items) + '\nTotal cost: BDT '+str(request.session['total'] + 65*request.session['pack'])+'\n'
            sub = 'Order Placed'
            # try:
            #     sendMail(email, sub, msg)
            # except:
            #     print('failed to send mail!')

            request.session['cart'] = {}
            request.session['productList'] = {}
            return redirect('my_orders')

        return redirect('homepage')


    else:
        return render(request,'bkashpay.html',{})


def verify_bkash(request):
    if request.method == 'POST':
        vc = request.POST.get('vc')


        acc = request.session['phone']
        cur = connection.cursor()
        cur.execute("select otp from BKASH where ACCNO=%s",[acc])
        result = cur.fetchone()
        otp = result[0]
        # pin = result[1]
        if vc:
            if int(vc) == otp:
                print('verified')
                return redirect('v_p')
            else:
                return render(request, 'bkashverification.html', {})

        else:
            print('failed!')
            return render(request,'bkashverification.html',{})
    else:
        print('verifying')
        return render(request,'bkashverification.html',{})

def get_items(request):

    productList = request.session.get('productList')
    print(productList)
    # getting products from cart.....
    cart = request.session.get('cart')
    # print(cart)
    cartkeys = list(cart.keys())
    items = []
    if cart:
        print('something is in cart!')
        for key in cartkeys:
            items.append(productList[key])
    else:
        print('cart is empty!')

    return items


def push_on_payment(paymentstatus,method):
    sqlonPayment = "INSERT INTO PAYMENTS(PAYMENT_ID, ORDER_ID, PAYMENT_STATUS, METHOD) VALUES (PAYMENTID.nextval,ORDERID.currval,%s,%s)"
    # paymentstatus = 'True'
    try:
        cur = connection.cursor()
        cur.execute(sqlonPayment, [paymentstatus, method])
        connection.commit()
        cur.close()
    except:
        print("failed to pay!")
        return redirect('cart')


def get_customer_id(email):
    sqlonPEOPLE = "SELECT CUSTOMER_ID FROM PEOPLE WHERE EMAIL=%s"
    try:
        cur = connection.cursor()
        cur.execute(sqlonPEOPLE, [email])
        result = cur.fetchone()
        cur.close()
        peopleid = result[0]
    except:
        print("couldn't find you logged in!")
        return redirect('login')

    return peopleid

def bkash_check(request):
    email = None
    try:
        email = request.session['email']

    except:
        print("couldn't find you logged in")
        return redirect('/home/login')
    try:
        cart = request.session.get('cart')

    except:
        return redirect('homepage')

    if len(cart) == 0:
        return redirect('homepage')
    request.session['verified'] = False
    request.session['acc'] = False
    if request.method == 'POST':
        phoneNo = request.POST.get('accno')
        request.session['phone'] = phoneNo
        otp = random.randrange(start=132457,step=1)
        print('acc not given')
        # try:
        phoneNo = int(phoneNo)
        print('phone:', end=' ')
        print(phoneNo)
        cur = connection.cursor()
        try:
            cur.execute("select ACCNO from BKASH where ACCNO = %s",[phoneNo])
            res = cur.fetchone()
            dbacc = res[0]
            if dbacc:

                cur.execute("UPDATE BKASH set OTP = %s where ACCNO=%s", [otp, phoneNo])
                connection.commit()
            else:
                return render(request, 'bkash.html',
                              {'msg:': "This account Doesn't exist!\nPlease Open an account through Bkash App"})
            request.session['acc'] = True

        except:
            request.session['acc'] = False
            print('not found the acc..')
            return render(request, 'bkash.html',
                          {'msg:': "This account Doesn't exist!\nPlease Open an account through Bkash App"})

        print(request.session['acc'])
        print('sending mail...')
        name = request.session['name']
        sub = 'Bkash Verification code'
        msg = 'Hello, ' + name + '\nYour verfication code: ' + str(otp)
        try:
            sendMail(email,sub,msg)
        except:
            print('failed to send mail!')
        print('mail sent!')
        return redirect('v_b')

    else:

        return render(request, 'bkash.html',{})


def credit_check(request):
    email = None
    try:
        email = request.session['email']
    except:
        print("couldn't find you logged in")
        return redirect('/home/login')
    try:
        cart = request.session.get('cart')
        key = list(cart.keys())

    except:
        return redirect('homepage')
    if len(key) == 0:
        return redirect('homepage')
    if request.method == 'POST':
        nameoncard = request.POST.get('cardname')
        cardno = request.POST.get('cardnumber')
        expdate = request.POST.get('expdate')
        cvv = request.POST.get('cvv')
        #
        items = get_items(request)
        # count = request.session['qty']
        peopleid = get_customer_id(email)
        print("people id : " + str(peopleid))
        orderdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(orderdate)

        '''Now put them on Product_Orders Table'''

        # push_on_product_orders(request,orderid)
        sqlonCreditcard = ("select CARD_NO, NAME_ON_CARD, EXP_DATE, CVV,ZIP_CODE from CREDIT_CARD where  CARD_NO=%s")

        '''setting payment_status and Credit_card for now. later it should be checked first!'''
        method = 'creditcard'

        print('i m here 2')
        CARD_NO = None
        NAME_ON_CARD = None
        EXP_DATE = None
        CVV = None
        try:
            cur = connection.cursor()
            cur.execute(sqlonCreditcard, [cardno])
            resultfromcard = cur.fetchall()
            cur.close()
            for r in resultfromcard:
                CARD_NO = r[0]
                NAME_ON_CARD= r[1]
                EXP_DATE = r[2]
                CVV= r[3]

        except:

            print('failed to get info from credentials!')
            return redirect('order_place')
        print("expdate: ", end = ' ')
        print(expdate)

        try:
            EXP_DATE = datetime.__format__(EXP_DATE,"%Y-%m-%d")
        except:
            return render(request,'check1.html',{'msg':'Wrong credentials. Try Again!'})
        if expdate == EXP_DATE:
            print('mathced date')
        elif expdate > EXP_DATE :
            print('ok!')
        else:
            print('expired!')
        print("EXP_DATE: ", end = ' ')
        print(EXP_DATE)

        if expdate == EXP_DATE and int(cardno) == CARD_NO and int(cvv) == CVV and nameoncard== NAME_ON_CARD :
            if  expdate >= datetime.now().strftime("%Y-%m-%d") :
                print('card verified!')
                '''making order and payment '''
                makeorder(request, peopleid, orderdate, 'True',method)
                # push_on_payment(orderid, paymentid, 'True', 'creditcard')
            else:
                return render(request,'check1.html',{'msg':'Your Credit Card is out of Date, Sir!'})

        else:
                print('card not found')
                print(CARD_NO,cardno,NAME_ON_CARD,CVV)
                return render(request,'check1.html',{'msg':'wrong credentials! try again'})
        print('i m here 3')
        date = datetime.now().strftime("%d-%m-%y %H:%M:%S")
        print(date)
        print('order successful!')

        '''sending a mail'''
        print('sending email..')

        name = request.session['name']
        msg = 'Hello, ' + name + '\nYour Order has Been Placed SuccessFully.\n' + 'We will reach you to reconfirm very soon!\n' + 'You Have ' + str(
            request.session['pack']) + ' packages in process to recieve' + '\nYour orders: \n' + str(
            items) + '\nTotal cost: BDT ' + str(request.session['total'] + 65*request.session['pack']) + '\n'
        sub = 'Order Placed'
        # try:
        #     sendMail(email, sub, msg)
        # except:
        #     print('failed to send mail!')

        request.session['cart'] = {}
        request.session['productList'] = {}
        return redirect('my_orders')

    else:
       return render(request,'check1.html',{})

def place_your_order(request):
    print("i m in orderplace!")

    try:
        product_dic,total_count,total,package = getProductdic(request)
    except:
        return redirect('homepage')
    print(product_dic,total_count,total)
    request.session['qty'] = total_count
    request.session['pack'] = package

    return render(request,'placeorder.html',{'products':product_dic, 'total_count':total_count,'total':total,'after_fee': total + 69*package,'fee':65*package})



def getProductdic(request):
    print('i m in getproductdic')
    try:
        keys = None
        car = request.session.get('cart')
        if car:
            keys = list(car.keys())
            if(len(keys))==0:
                return redirect('homepage')
            package = len(keys)
            pro_url = request.session.get('pro_url')
            prokeys = list(pro_url.keys())
        else:
            return redirect('homepage')
    except:
        return redirect('/home')
    if (len(keys)) == 0:
        return redirect('homepage')
    # keys = cart.keys()
    # print(keys)
    print(car)

    product_dic = []
    total = 0
    total_count = 0
    cur = connection.cursor()
    for id in keys:
        if id != 'null':
            id = int(id)
            # print(id)
            cur.execute("select PRODUCT_NAME,PRICE,DESCRIPTION,SHOP_ID from PRODUCTS where PRODUCT_ID=%s", [id])
            result = cur.fetchone()
            name = result[0]
            price = result[1]
            desc = result[2]
            shop_id = result[3]
            shopname  = 'Myshop'
            try:
                cur.execute("select SHOP_NAME from SHOPS where SHOP_ID =%s",[shop_id])
                r1 = cur.fetchone()
                shopname = r1[0]
            except:
                print('no shop related to this!')
            try:
                photo_url = pro_url[str(id)]
                # print('photo:' + photo_url)
            except:
                photo_url = 'uploads/products/product.jpg'
                # print('photo: ' + photo_url)

            quantity = int(car[str(id)])
            total += quantity * price
            total_count += quantity
            request.session['total'] = total

            row = {'name': name,'shop':shopname, 'price': price, 'product_img': photo_url, 'specs': desc, 'id': id,
                   'quantity': quantity, 'price_total': quantity * price}
            product_dic.append(row)
    cur.close()
    print(product_dic,total,total_count,package)
    return product_dic,total_count,total,package

def editBillingAdress(request):
    email = None
    try:
        email = request.session['email']
    except:
        print('in acc settings failed to get username')
        return redirect('/home/login')
    print("i m billing")
    # print(username)
    if request.method == 'POST':
        print("reached!")
        cursor = connection.cursor()
        fname = request.POST.get('fname')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        postcode = request.POST.get('zip')
        city = request.POST.get('city')
        flat = request.POST.get('flat')
        deliveryat = 'Name: '+ fname +'\ncontact: ' + str(phone)+ '\nAddress: '+ address + ', '+city + '.' +'\nPostcode: '+ postcode + '\nRoom/Flat: ' +flat + '\n'
        request.session['deliveryat'] = deliveryat

        try:
            cur = Initiate_Cursor()
            cur.execute("Update people set BILLING_ADDRESS= %s where EMAIL=%s",[deliveryat,email])
        except:
            print('bill not updated!')

        print('''it's done updating your info!''')
        return redirect('order_place')
    else:
        return render(request, 'billingAdress.html', {})


def cash_on_delivery(request):
    try:
        email = request.session['email']
        print(email)
    except:
        return redirect('login')
    peopleid = get_customer_id(email)
    orderdate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    method = 'cash_on_delivery'
    try:
        makeorder(request, peopleid, orderdate, 'False', method)

    except:
        return redirect('cart')
    name = request.session['name']
    items = get_items(request)




    '''empty the cart and redirect to orderList'''
    request.session['cart'] = {}
    request.session['productList'] = {}
    return redirect('my_orders')
# def pay_bkash(request,paymentid):
#     try:
#         email = request.session['email']
#     except:
#         print('log in to pay')
#         return redirect('login')
#     if request.method == 'POST':
#         otp = random.randrange(start=135792,step=1)
#         try:
#             bkashno = request.POST.get('accno')
#             request.session['bkash'] = True
#         except:
#             print('failed to catch your baksh acc')
#             return redirect('bkash')
#         if bkashno:
#             try:
#                 v_c = request.POST.get('vc')
#             except:
#                 return redirect('bkash')
#             pin = None
#             if v_c:
#                 try:
#                     pin = request.POST.get('pin')
#                 except:
#                     pin = 0
#                     return ('bkash')
#             else:
#                 return redirect('pay_bkash')
#             # bkash(bkashno,otp,paymentid,pin)
#
#         return redirect('confirm_order')
#     else:
#         return  render(request,'bkash.html',{})
#

def Initiate_Cursor():
    cursor = connection.cursor()
    return cursor


def sendMail(email,subject,msg):
    send_mail(
        subject,
        msg,
        EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )

