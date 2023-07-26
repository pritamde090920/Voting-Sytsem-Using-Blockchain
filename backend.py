from flask import Flask,render_template,request,session,redirect,url_for,send_file,flash
import mysql.connector
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField
from wtforms.validators import InputRequired
from email.message import EmailMessage
import random
import ssl
import smtplib
import datetime


# DAPP Requirements
from hexbytes import HexBytes
from web3.auto import w3
import json
from web3 import Web3, HTTPProvider


app = Flask(__name__)
BOOTSTRAP = Bootstrap(app)
app.config['SECRET_KEY'] = 'TempSecretKey'
#app.secret_key="super secret key"

l1,l2,l3=list(),dict(),list()
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="123456",
  database="votingsystem",
  auth_plugin='mysql_native_password'
)

cursor = mydb.cursor()

w3 = Web3(HTTPProvider("HTTP://127.0.0.1:7545"))
#print(w3.isConnected())

truffleFile = json.load(open('./build/contracts/modifiedVotingSystem.json'))
abi = truffleFile['abi']
bytecode = truffleFile['bytecode']

#print(abi)

contract_address='0x8178Fd75095BaB81f97a0A38595A0FAC346211Ec'

VOTEBALLOT = w3.eth.contract(abi=abi, address=contract_address)

chain_id=1337
admin='0x73ff0213A6b2B4647eeaFa80023AB46de3984c28'
Accounts=['0xf4f5a84a58048a3656728a27E5f5Fec96cef4b55']
privateKeys=['0xb85e7747fa90f8dc81cd536be637c05f1ba864e5c925474329bee641afd7e4b9']

#print(w3.eth.get_block('latest').tr)
#print(VOTEBALLOT.functions.getVoteCount().call())
#alreadyVoted=VOTEBALLOT.functions.getVoterId().call()
#print(alreadyVoted)



class OtpVerificationForm(FlaskForm):
    otp=StringField('Enter Otp', [InputRequired()])

cursor.execute("SELECT * from candidateDetails")
lst=cursor.fetchall()
print(lst)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/otpValidation", methods=['GET'])
def otpValidation():
    sender='voting.system023@gmail.com'
    password='ccswdosuwixyeaaw'
    cursor.execute("SELECT email from voterlogin where name=%s and voterID=%s",(session['votername'],session['voterID']))
    record=cursor.fetchone()
    receiver=record[0]
    subject='OTP for Voting Authentication'
    otp_val=random.randrange(100000,999999)
    session['otp']=otp_val
    name=session['votername']
    body="Hello "+str(name)+",\nYour One Time Password(OTP) for pre-voting authentication is : "+str(otp_val)+"\nThe OTP is valid for 60 seconds"
    em=EmailMessage()
    em['From']=sender
    em['To']=receiver
    em['Subject']=subject
    em.set_content(body)
    context=ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
        smtp.login(sender,password)
        smtp.sendmail(sender,receiver,em.as_string())
    
    val=datetime.datetime.now()
    date=str(val.year)+str(val.month)+str(val.day)
    time=(val.hour)*3600+(val.minute)*60+(val.second)
    session['date']=date
    session['time']=time
    
    form=OtpVerificationForm()
    return render_template("otpValidation.html",otpverificationform=form)

@app.route("/otp", methods=['POST'])
def otp():
    otp=request.form["otp"]
    val=datetime.datetime.now()
    date=str(val.year)+str(val.month)+str(val.day)
    time=(val.hour)*3600+(val.minute)*60+(val.second)
    flag=False
    if date==session['date']:
        if(time-int(session['time'])<=60):
            flag=True
    elif date==(int(session['date'])+1):
        if(86400-int(session['time'])+time)<=60:
            flag=True
        
    if otp==str(session['otp']) and flag:
        return redirect(url_for('castVote'))
    return redirect(url_for('voterdashboard'))

@app.route("/votingTime",methods=['GET'])
def votingTime():
    return render_template("votingTime.html")

@app.route("/startVote")
def startVote():
    VOTEBALLOT.functions.startElection().transact({'from':admin})
    if VOTEBALLOT.functions.getStart().call():
        msg="Voting Process has been successfully started!!"
        return render_template("votingProcessStatus.html",msg=msg)
    return "something is wrong"

@app.route("/endVote")
def endVote():
    VOTEBALLOT.functions.endElection().transact({'from':admin})
    msg="Voting Process has been successfully ended!!" 
    return render_template("votingProcessStatus.html",msg=msg)

@app.route("/castVote")
def castVote():
    if VOTEBALLOT.functions.getStart().call()==False:
        msg="Voting Process is yet to start.Please Wait!!"
        return render_template("votingProcessVoter.html",msg=msg)
    cursor.execute("SELECT * from voterlogin where name=%s and voterID=%s",(session['votername'],session['voterID']))
    record=cursor.fetchall()
    details=[record[0][0],record[0][1],record[0][5],record[0][6],record[0][7],record[0][8]]
    valid=record[0][3]
    can_det=list()
    if record[0][8]=='pe':
        cursor.execute("SELECT ucid,name,party,valid from candidatedetails where state=%s and pc=%s and toe=%s",(record[0][5],record[0][6],record[0][8]))
        record=cursor.fetchall()
    else:
        cursor.execute("SELECT ucid,name,party,valid from candidatedetails where state=%s and pc=%s and ac=%s and toe=%s",(record[0][5],record[0][6],record[0][7],record[0][8]))
        record=cursor.fetchall()
    for i in record:
        if i[-1]==True:
            can_det.append(i[:-1])
            
    if valid==True:
        #form = VotingForm()
        return render_template('voteCast.html',can_det=can_det,details=details)

    else:
        return render_template('voterNotValidated.html')


@app.route("/validateVoter", methods=['GET','POST'])
def validateVoterPage():
    record,validated=list(),list()
    cursor.execute("SELECT name,voterID,email,state,pc,ac,toe,validated from voterlogin")
    for i in cursor:
        t=list(i)
        if t[-1]==False:
            t.append("NO")
        else:
            t.append("YES")
        t.pop(-2)
        record.append(t)
        
    return render_template('validateVoter.html',details=record)

@app.route("/voterValidateSuccess<number>", methods=['GET','POST'])
def validateVoter(number):
    cursor.execute("update voterlogin set validated=%s where voterID=%s",(1,number))
    mydb.commit()

    return redirect(url_for('validateVoterPage'))


@app.route("/addCandidate", methods=['GET'])
def addCandidate():
    record=list()
    cursor.execute("SELECT name,party,state,pc,ac,toe,status,ucid,nom,valid from candidatedetails")
    for i in cursor:
        t=list(i)
        if t[-2]==False:
            t[-2]="NO"
        else:
            t[-2]="YES"
        if t[-1]==False:
            t[-1]="NO"
        else:
            t[-1]="YES"
        record.append(t)
        
    return render_template('addCandidate.html',details=record)

@app.route("/candidateValidateSuccess<number>", methods=['GET','POST'])
def validateCandidate(number):
    if number=="NO":
        cursor.execute("update candidatedetails set nom=%s,valid=%s where ucid=%s",(0,0,session['ucid']))
    else:
        cursor.execute("update candidatedetails set valid=%s where ucid=%s",(1,session['ucid']))
    mydb.commit()

    return redirect(url_for('addCandidate'))

@app.route("/voterdashboard")
def voterdashboard():
    return render_template("voterdashboard.html",name=session['votername'])

@app.route("/candidatedashboard")
def candidatedashboard():
    return render_template("candidatedashboard.html",name=session['candidatename'])

@app.route("/candidateRegister")
def candidateRegister():
    file=open("Constituencies.csv",'r')
    file1=file.readlines()
    states,values=list(),list()
    for i in file1[2:]:
        t=i.split(',')
        t[-1]=t[-1][:-1]
        values.append(t)
        if t[0] not in states:
            states.append(t[0])
    file.close()
    return render_template("candidateRegistration.html",states=states,values=values)

@app.route("/candidateRegistration",methods=['GET','POST'])
def candidateRegistration():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password_enter=request.form['password']
        
        sender='voting.system023@gmail.com'
        password='ccswdosuwixyeaaw'
        receiver=email
        subject='Unique Candidate ID For Voting System'
        cursor.execute("SELECT distinct ucid from candidatedetails")
        record=cursor.fetchall()
        while(True):
            ucid=random.randrange(100000,999999)
            if ucid not in record:
                break
        body="Hello "+str(name)+",\nYour Unique Candidate ID(UCID) fro Voting System is : "+str(ucid)
        em=EmailMessage()
        em['From']=sender
        em['To']=receiver
        em['Subject']=subject
        em.set_content(body)
        context=ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
            smtp.login(sender,password)
            smtp.sendmail(sender,receiver,em.as_string())
        
        cursor.execute("SELECT * from candidatedetails where name=%s and ucid=%s",(name,ucid))
        record = cursor.fetchall()
        if len(record)>0:
            return "You are already registered!Try to Login."
        else:
            cursor.execute("insert into candidatedetails values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(name,None,None,None,None,None,None,password_enter,email,ucid,0,0))
            mydb.commit()
            return render_template('sucess.html')

@app.route('/candidatelogin',methods=['GET','POST'])
def candidatelogin():
    msg=''
    if request.method=='POST':
        name=request.form['name']
        ucid=request.form['ucid']
        password=request.form['password']
        cursor.execute("SELECT * from candidatedetails where name=%s and ucid=%s and password=%s",(name,ucid,password))
        record = cursor.fetchall()
        if record:
            session['loggedin']=True
            session['candidatename']=record[0][0]
            session['ucid']=record[0][9]
            session['email']=record[0][8]
            return redirect(url_for('candidatedashboard'))
        else:
            msg='Incorrect credentials.Please try again!'
    return render_template('candidatelogin.html',msg=msg)

@app.route("/addNomination")
def addNomination():
    file=open("Constituencies.csv",'r')
    file1=file.readlines()
    states,values=list(),list()
    for i in file1[2:]:
        t=i.split(',')
        t[-1]=t[-1][:-1]
        values.append(t)
        if t[0] not in states:
            states.append(t[0])
    file.close()
    
    cursor.execute("SELECT nom from candidatedetails where name=%s and ucid=%s",(session['candidatename'],session['ucid']))
    record=cursor.fetchall()
    if record[0][0]==False:
        return render_template('addNomination.html',name=session['candidatename'],email=session['email'],ucid=session['ucid'],states=states,values=values)
    else:
        return render_template('nominationSuccess.html')

@app.route("/submitNomination",methods=['GET','POST'])
def submitNomination():
    if request.method=='POST':
        party=request.form['party']
        status=request.form['status']
        state=request.form['slct1']
        pc=request.form['slct2']
        ac=request.form['slct3']
        toe=request.form['toe']

        if toe=="ae" and ac=="-- Choose assembly constituency --":
                return redirect(url_for('addNomination'))
        elif ac=="Not Required":
            cursor.execute("update candidatedetails set party=%s,state=%s,pc=%s,ac=%s,toe=%s,status=%s,nom=%s where ucid=%s",(party,state,pc,None,toe,status,1,session['ucid']))
            mydb.commit()
        else:
            cursor.execute("update candidatedetails set party=%s,state=%s,pc=%s,ac=%s,toe=%s,status=%s,nom=%s where ucid=%s",(party,state,pc,ac,toe,status,1,session['ucid']))
            mydb.commit()

        return render_template('nominationSuccess.html')

@app.route("/nominationStatus")
def nominationStatus():
    cursor.execute("SELECT valid,nom from candidatedetails where name=%s and ucid=%s",(session['candidatename'],session['ucid']))
    record=cursor.fetchall()
    return render_template('nominationStatus.html',validated=record[0][0],nom=record[0][1])



@app.route("/admindashboard")
def admindashboard():
    return render_template("admindashboard.html",name=session['adminname'])


@app.route('/voterlogin',methods=['GET','POST'])
def voterlogin():
    msg=''
    if request.method=='POST':
        name=request.form['name']
        epicnumber=request.form['epicnumber']
        password=request.form['password']
        cursor.execute("SELECT * from voterlogin where name=%s and voterID=%s and password=%s",(name,epicnumber,password))
        record = cursor.fetchall()
        if record:
            session['loggedin']=True
            session['votername']=record[0][0]
            session['voterID']=record[0][1]
            return redirect(url_for('voterdashboard'))
        else:
            msg='Incorrect credentials.Please try again!'
    return render_template('voterlogin.html',msg=msg)

@app.route("/logOut")
def logOut():
    session.pop('loggedin',None)
    session.pop('name',None)
    return redirect(url_for('home'))

@app.route("/voterRegistration",methods=['GET','POST'])
def voterRegistration():
    if request.method=='POST':
        name=request.form['name']
        epicnumber=request.form['epicnumber']
        password=request.form['password']
        email=request.form['email']
        state=request.form['slct1']
        pc=request.form['slct2']
        ac=request.form['slct3']
        toe=request.form['toe']
        cursor.execute("SELECT * from voterlogin where name=%s and voterID=%s and password=%s and email=%s and state=%s and pc=%s and ac=%s",
                       (name,epicnumber,password,email,state,pc,ac))
        record = cursor.fetchall()
        if len(record)>0:
            return "You are already registered!Try to Login."
        else:
            if toe=="ae" and ac=="-- Choose assembly constituency --":
                return redirect(url_for('voterRegister'))
            if ac=="Not Required":
                cursor.execute("insert into voterlogin values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(name,epicnumber,password,0,email,state,pc,None,toe))
                mydb.commit()
                return render_template('sucess.html')
            else:
                cursor.execute("insert into voterlogin values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(name,epicnumber,password,0,email,state,pc,ac,toe))
                mydb.commit()
                return render_template('sucess.html')

@app.route("/voterRegister")
def voterRegister():
    file=open("Constituencies.csv",'r')
    file1=file.readlines()
    states,values=list(),list()
    for i in file1[2:]:
        t=i.split(',')
        t[-1]=t[-1][:-1]
        values.append(t)
        if t[0] not in states:
            states.append(t[0])
    file.close()
    return render_template("voterRegistration.html",states=states,values=values)



@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    msg=''
    if request.method=='POST':
        name=request.form['adminname']
        adminID=request.form['adminid']
        password=request.form['password']
        cursor.execute("SELECT * from adminlogin where name=%s and adminID=%s and password=%s",(name,adminID,password))
        record = cursor.fetchall()
        if record:
            session['loggedin']=True
            session['adminname']=record[0][0]
            return render_template("admindashboard.html",name=session['adminname'])
        else:
            msg='Incorrect credentials.Please try again!'
    return render_template('adminlogin.html',msg=msg)

@app.route('/viewResultAdm',methods=['GET','POST'])
def viewResultAdm():
    if VOTEBALLOT.functions.getEnd().call()==False:
        msg="Result will be displayed at the end of the voting!!"
        return render_template("votingProcessStatus.html",msg=msg)
    voteCount=dict()
    res=VOTEBALLOT.functions.getVoteCount().call()
    if request.method=='POST':
        state=request.form['slct1']
        pc=request.form['slct2']
        ac=request.form['slct3']
        toe=request.form['toe']

        if ac=="Not Required":
            cursor.execute("select name,party,ucid from candidatedetails where state=%s and pc=%s and toe=%s",(state,pc,toe))
        else:
            cursor.execute("select name,party,ucid from candidatedetails where state=%s and pc=%s and ac=%s and toe=%s",(state,pc,ac,toe))
        record=cursor.fetchall()
        can_det=[i for i in record]
        d,l=dict(),list()
        for i in can_det:
            d[i[2]]=d.get(i[2],0)
            l.append(i[2])
        for i in res:
            if i in l:
               d[i]+=1
        print(can_det)   
        return render_template('viewResultAdm.html',result=d,can_det=can_det)

@app.route('/viewResultVot')
def viewResultVot():
    if VOTEBALLOT.functions.getEnd().call()==False:
        msg="Result will be displayed at the end of the voting!!"
        return render_template("votingProcessVoter.html",msg=msg)
    voteCount=dict()
    res=VOTEBALLOT.functions.getVoteCount().call()
    name=session['votername']
    voterid=session['voterID']

    cursor.execute("select state,pc,ac,toe from voterlogin where name=%s and voterID=%s",(name,voterid))
    record=cursor.fetchall()
    state=record[0][0]
    pc=record[0][1]
    ac=record[0][2]
    toe=record[0][3]

    if ac is None:
        cursor.execute("select name,party,ucid from candidatedetails where state=%s and pc=%s and toe=%s",(state,pc,toe))
    else:
        cursor.execute("select name,party,ucid from candidatedetails where state=%s and pc=%s and ac=%s and toe=%s",(state,pc,ac,toe))
    record=cursor.fetchall()
    can_det=[i for i in record]
    d,l=dict(),list()
    for i in can_det:
        d[i[2]]=d.get(i[2],0)
        l.append(i[2])
    for i in res:
        if i in l:
           d[i]+=1

    return render_template('viewResultVot.html',result=d,can_det=can_det)    

@app.route('/viewResultCan')
def viewResultCan():
    if VOTEBALLOT.functions.getEnd().call()==False:
        msg="Result will be displayed at the end of the voting!!"
        return render_template("votingProcessCandidate.html",msg=msg)
    voteCount=dict()
    res=VOTEBALLOT.functions.getVoteCount().call()
    ucid=session['ucid']

    cursor.execute("select state,pc,ac,toe from candidatedetails where ucid=%s",[ucid])
    record=cursor.fetchall()
    state=record[0][0]
    pc=record[0][1]
    ac=record[0][2]
    toe=record[0][3]

    if ac is None:
        cursor.execute("select name,party,ucid from candidatedetails where state=%s and pc=%s and toe=%s",(state,pc,toe))
    else:
        cursor.execute("select name,party,ucid from candidatedetails where state=%s and pc=%s and ac=%s and toe=%s",(state,pc,ac,toe))
    record=cursor.fetchall()
    can_det=[i for i in record]
    d,l=dict(),list()
    for i in can_det:
        d[i[2]]=d.get(i[2],0)
        l.append(i[2])
    for i in res:
        if i in l:
           d[i]+=1

    return render_template('viewResultCan.html',result=d,can_det=can_det)

@app.route('/viewResultOptionsAdm')
def viewResultOptionsAdm():
    file=open("Constituencies.csv",'r')
    file1=file.readlines()
    states,values=list(),list()
    for i in file1[2:]:
        t=i.split(',')
        t[-1]=t[-1][:-1]
        values.append(t)
        if t[0] not in states:
            states.append(t[0])
    file.close()

    cursor.execute("SELECT * from candidatedetails")
    record=cursor.fetchall()
    return render_template('viewResultOptionsAdm.html',can_det=record,states=states,values=values)


@app.route("/voteAdded<voterID>)", methods=['POST'])
def voteAdded(voterID):
    alreadyVoted=VOTEBALLOT.functions.getVoterId().call()
    if voterID in alreadyVoted:
        #flash('Vote has already been cast with this voter ID!!', 'success')
        return "You have already Voted!Not allowed to vote again!"
        return render_template(
            'voterDashboard.html',name=session['name']
        )
    castedVote=request.form["options"]
    """cursor.execute("SELECT ether_address from voterlogin where voterID=%s",voterID)
    ethereum_address = cursor.fetchone()"""
    #eth_add=0
    #print(request.form['voter_id'])
    #for i in range(len(choices)):
        #if ethereum_address[0] in choices[i]:
            #eth_add=i
    nonce= w3.eth.getTransactionCount(Accounts[0])
    call_contract_function = VOTEBALLOT.functions.requestVoter(
        voterID,
        Accounts[0],castedVote).buildTransaction({"gasPrice": w3.eth.gas_price, 
    "chainId": chain_id, 
    "from": Accounts[0], 
    "nonce": nonce})
    

    signed_tx = w3.eth.account.sign_transaction(call_contract_function, privateKeys[0])
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    VOTEBALLOT.functions.verifyVoter(Accounts[0]).call()
    voted=0
    for i in range(len(l1)):
        if castedVote in l1[i]:
            voted=i+1
            break
    VOTEBALLOT.functions.vote(voted,Accounts[0]).call()
    #transaction_info = w3.eth.getTransaction(call_contract_function)
    msg=''
    
    #l3.append(request.form['voter_id'])
    #l2[castedVote]+=1
    
    return render_template(
        'voteDone.html'
        )

if __name__=="__main__":
    app.run(debug=True)
