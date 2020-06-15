print("")
print("*****************************************************")
print("*                     WELCOME                       *")
print("*                                                   *")
print("*                    FingerTips                     *")
print("*                                                   *")
print("*                                                   *")
print("*****************************************************")

print("")
print ("-----starting application-----")
print("")

import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library
import time
from datetime import datetime  #for time stamps
import smbus
import pyrebase  #to connect to firebase
import os       #for text-to-speech conversion
GPIO.setwarnings(False)  # Ignore warning for now
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
# Set pin 10 to be an input pin and set initial value to be pulled low (off)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #input button at pin-10 on raspberry pi
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #input button at pin-22 on raspberry pi


token_timer=time.time() #time stamp for token refresh every hour

#initializing values
i = 0
t1 = -1
t2 = -1
flag = 1
final_code = ""
final_string=""
stream_flag = 1
stream_count =0


#config of your firebase project
config = {
  "apiKey": "your-api-key",
  "authDomain": "your-project-id.firebaseapp.com",
  "databaseURL": "https://your-database-name.firebaseio.com",
  "storageBucket": "your-project-id.appspot.com"
}

firebase = pyrebase.initialize_app(config)

print ("-----Initialization Success-----")
print("")

# Get a reference to the auth service
auth = firebase.auth()

# Log the user in
user = auth.sign_in_with_email_and_password("email-id", "password")

print ("-----Sign-in Success-----")
print("")

# Get a reference to the database service
db = firebase.database()

print ("-----db Initialized-----")
print("")

user = auth.refresh(user['refreshToken'])   #token refresh


# Define some device parameters
I2C_ADDR  = 0x3f # I2C device address(device adress is variable)
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

def lcd_init():
        # Initialise display
        lcd_byte(0x33,LCD_CMD) # 110011 Initialise
        lcd_byte(0x32,LCD_CMD) # 110010 Initialise
        lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
        lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
        lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
        lcd_byte(0x01,LCD_CMD) # 000001 Clear display
        time.sleep(E_DELAY)

def lcd_byte(bits, mode):
        # Send byte to data pins
        # bits = the data
        # mode = 1 for data
        #        0 for command

        bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
        bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

        # High bits
        bus.write_byte(I2C_ADDR, bits_high)
        lcd_toggle_enable(bits_high)

        # Low bits
        bus.write_byte(I2C_ADDR, bits_low)
        lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
        # Toggle enable
        time.sleep(E_DELAY)
        bus.write_byte(I2C_ADDR, (bits | ENABLE))
        time.sleep(E_PULSE)
        bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
        time.sleep(E_DELAY)

def lcd_string(message,line):
        # Send string to display

        message = message.ljust(LCD_WIDTH," ")

        lcd_byte(line, LCD_CMD)

        for i in range(LCD_WIDTH):
                lcd_byte(ord(message[i]),LCD_CHR)
 

def add_code(code):
        global final_code
        final_code += code
        #print(final_code)

def process(signal):  #converts signal to dot/dash based on signal length
        if(signal > 0 and signal < 0.3):
                add_code('.')
        if(signal >= 0.3 and signal < 1.5):
                add_code('-')
        if(signal >=1.5):
                add_code('/')


def main_code(): 
        global t1, flag, t2
        while GPIO.input(10) == GPIO.HIGH:
                if flag == 1:
                        t1 = time.time()
                        flag = 0

        if(t1 > -1 and flag == 0):
                t2 = time.time()
                signal_len = (t2-t1)
                process(signal_len)
                flag = 1
                t1 = -1


def converter(code):   #to convert the morse code into alphabets
        global final_string
        letters = [".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....", "..", ".---", "-.-", ".-..", "--","-.", "---", ".--.", "--.-", ".-.", "...", "-", "..-", "...-", ".--", "-..-", "-.--", "--..", "E"]
        i = 0

        if (code == ".-.-.-"): #for full stop
                print(".")
                #time.sleep(0.2)

        elif (code == ".-.-"): #for space
                final_string+=" "
                print("--space--")
                #time.sleep(0.2)

        elif (code == "....."): #for backspace
                final_string = final_string[:-1]
                print(final_string)
                lcd_string(final_string,LCD_LINE_1)
        
        elif (code == "-...-"):  #to clear the string(message)
                final_string = ""
                lcd_string(final_string,LCD_LINE_1)
                print("Message cleared.")

        elif (code == "..-.."):         #shortcut message
                final_string = "HELLO THERE"
                lcd_string(final_string,LCD_LINE_1)
                print(final_string)
        
        elif (code == "...---..."):   #emergency input
                print ("SOS")
                final_string = "S O S"
                lcd_string(final_string,LCD_LINE_1)
                time.sleep(1)
                lcd_string("",LCD_LINE_1)
                lcd_string("",LCD_LINE_2)

                data = {"messageUser": "Jyotsna Dsilva","messageText":final_string,"messageTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S")} #data to save
                results = db.push(data, user['idToken'])  #send to database
                print("---message sent---")
                print("waiting for text to speech....")
                os.system("espeak '"+final_string+"' 2>/dev/null")  #for text-to-speech output
                print("---TTS Successful---")
                print("")
                final_string = ""

        elif (GPIO.input(22) == GPIO.HIGH):    #send button with text-to-speech conversion
                print("Sending...")
                data = {"messageUser": "Jyotsna Dsilva","messageText":final_string,"messageTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}  #data to save
                results = db.push(data, user['idToken']) #send to database
                print("---Message Sent---")
                senta="Message Sent."
                lcd_string(senta,LCD_LINE_2) #display on LCD
                time.sleep(1)
                lcd_string("",LCD_LINE_1)
                lcd_string("",LCD_LINE_2)
                print("TTS Initioation...")
                print("")
                os.system("espeak '"+final_string+"' 2>/dev/null")
                print("---TTS Successfull---")
                print("")
                time.sleep(2)
                
                final_string = "" #reset the string before next input
        
        elif (code == "/"):   #code to send the message without TTS conversion
                print("Sending...")
                data = {"messageUser": "Jyotsna Dsilva","messageText":final_string,"messageTime": datetime.now().strftime("%d-%m-%Y %H:%M:%S")}  #data for the database
                results = db.push(data, user['idToken'])  #data sending
                print("---message sent---")
                senta="Message Sent."
                lcd_string(senta,LCD_LINE_2)    # to display in LCD
                time.sleep(1)
                lcd_string("",LCD_LINE_1)
                lcd_string("",LCD_LINE_2)
                
                final_string = ""

        else:
                while (letters[i] != "E"):              #for valid inputs
                        if (letters[i] == code):
                                #print((chr(65 + i)))
                                final_string+=(chr(65 + i))
                                print(final_string)
                                lcd_string(final_string,LCD_LINE_1)
                                lcd_string("TYPING...",LCD_LINE_2)
                                
                                break

                        i = i+1

                        if (letters[i] == "E"): #for invalid inputs
                                final_code = ""
                                time.sleep(0.1)


def main():
        # Main program block
        # Initialise display
        lcd_init()


def stream_handler(message):    #handles stream function

        #print(message["event"]) # put
        #print(message["path"]) # /-K7yGTTEp7O549EzTYtI
        #print(message["data"]) # {'title': 'Pyrebase', "body": "etc..."}
        global stream_count
        global stream_flag 
        stream_count +=1
        new_message = message["data"]
        msg = str(new_message)

        print("---stream initiated---",stream_count)  
        print("")
        
        x = "'messageUser': 'Jyotsna Dsilva'" not in msg
        
        if(stream_count > 1 and x):
                stream_flag = 0
                save_str = final_string
                #print("if  cond...",stream_count)
                #print(msg)
                print("")

                msg2 = msg.replace("'"," ") #removes extra characters from msg
                msg3 = msg2.replace("{"," ")
                msg4=msg3.replace("}"," ")
                split_words =msg4.split(",")   #[messageText : hello World, messageTime:time,  messageUser: user_name]
                messageText = split_words[0].split(":")  #[messageText, hello World]
                messageTime = split_words[1].split(":")  #[messageTime, time]
                messageUser = split_words[2].split(":")  #[messageUser, user-name]

                final_data_msg = messageText[1].strip() #hello World
                final_data_time = messageTime[1].strip() #time
                f2_data_time = messageTime[2].strip()
                f3_data_time = messageTime[3].strip()
                final_data_user = messageUser[1].strip() #user-name


                print("[New Message]",final_data_user," : ", final_data_msg,"[",final_data_time,"   ",":",f2_data_time,":",f3_data_time,"]")
                print("")

                lcd_string("",LCD_LINE_1)
                lcd_string("",LCD_LINE_2)

                lcd_string(final_data_msg,LCD_LINE_1)
                lcd_string(final_data_user,LCD_LINE_2)
                
                print("TTS Initiation...")
                os.system("espeak '"+final_data_msg+"' 2>/dev/null") #for text-to-speech output
                print("---TTS Successful---")
                print("")
                print(final_string)
                print("Continue Typing...")

                time.sleep(10)          #displays the recieved message for 10 seconds 

                lcd_string(save_str,LCD_LINE_1)
                lcd_string("Typing...",LCD_LINE_2)
                
                
        
        elif(stream_count == 1):
                print("")
                print("Start typing...")
                print("")

        else:
                print("")
                print("type Something...")
                lcd_string("",LCD_LINE_2)
                lcd_string("Type Someting...",LCD_LINE_2)


my_stream = db.stream(stream_handler)          #listens whenever there is change in database

lcd_string("***Fingertips***",LCD_LINE_1) #to display when the application starts running
lcd_string("___Welcome___",LCD_LINE_2)

time.sleep(1)

lcd_string("",LCD_LINE_1)
lcd_string("Start typing...",LCD_LINE_2)


 
while True:               #run forever

        main_code()       #call the function for button clicks
        if(time.time() - t2 > 1):
                converter(final_code)
                final_code=""
                main_code() 

        if(time.time() - token_timer >= 3600):          #for refreshing database user token every hour
                user = auth.refresh(user['refreshToken'])
                print("---token refreshed---")
                token_timer = time.time()  

    

if __name__ == '__main__':

        try:
                main()
        except KeyboardInterrupt:
                pass
        finally:
                lcd_byte(0x01, LCD_CMD)             