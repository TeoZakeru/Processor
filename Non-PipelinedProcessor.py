class MIPSProcessor:
    def __init__(self):
        self.registers = [0] * 32 #initialising registers and memory to 0
        self.memory = [0] * 100
        self.pc = 0
        self.clock_cycles=0
        # t1-9 t2-10  t7-15  s2-18 s3-19
        #t1,t2,t3 t1(n)=5 t2(input)=0 t3(output)=10
        self.registers[9]=5  # t1=n=5
        self.registers[10]=0 #t2=0
        self.registers[11]=24 #t3=24
        self.memory[0]=5 #initialising values in memory
        self.memory[4]=7
        self.memory[8]=6
        self.memory[12]=2
        self.memory[16]=4

    def IF(self,machine_code): #this method fetches the instruction
        self.instruction = machine_code[self.pc]
        self.clock_cycles+=1#incrementing the clock cycles by 1
    
    def ID(self): #this method decodes the instruction and identifies the opeation and operand registers/immediate values
        self.opcode = self.instruction[:6]#extracting the opcode
        if self.opcode == '000000': #checking the opcode on a case by case basis
            #for R-type instruction
            funct = self.instruction[-6:]#extracting the funct value
            if funct == '100000':  # add
                self.rd = int(self.instruction[16:21], 2)
                self.rs = int(self.instruction[6:11], 2)
                self.rt = int(self.instruction[11:16], 2)
            elif funct == '100010':  # sub
                self.rd = int(self.instruction[16:21], 2)
                self.rs = int(self.instruction[6:11], 2)
                self.rt = int(self.instruction[11:16], 2)
            elif funct == '101010':  # slt
                self.rd = int(self.instruction[16:21], 2)
                self.rs = int(self.instruction[6:11], 2)
                self.rt = int(self.instruction[11:16], 2)
        #for R-type instruction
        elif self.opcode=='011100': #mul
            self.rd = int(self.instruction[16:21], 2)
            self.rs = int(self.instruction[6:11], 2)
            self.rt = int(self.instruction[11:16], 2)
        #for I-type instruction
        elif self.opcode == '100011': # lw
            self.rs = int(self.instruction[6:11], 2)
            self.rt = int(self.instruction[11:16], 2)
            self.imm = int(self.instruction[16:], 2)
        #for I-type instruction
        elif self.opcode == '101011': #sw
            self.rs = int(self.instruction[6:11], 2)
            self.rt = int(self.instruction[11:16], 2)
            self.imm = int(self.instruction[16:], 2)
        #for I-type instruction
        elif self.opcode == '001000': # addi
            self.rs = int(self.instruction[6:11], 2)
            self.rt = int(self.instruction[11:16], 2)
            if(self.instruction[16]=='1'):
                imm_binary = ''.join('1' if bit == '0' else '0' for bit in self.instruction[16:])
                self.imm = -(int(imm_binary, 2) + 1)
            else:     
                self.imm = int(self.instruction[16:], 2)
        #for J-type instruction
        elif self.opcode== '000010':#jump
            self.jump_address=int(self.instruction[6:],2)
        #for I-type instruction beq and bne
        elif self.opcode=='000100' or self.opcode=='000101':#beq and bne
            self.rs = int(self.instruction[6:11], 2)
            self.rt = int(self.instruction[11:16], 2)
            if(self.instruction[16]=='1'):
                imm_binary = ''.join('1' if bit == '0' else '0' for bit in self.instruction[16:])
                self.imm = -(int(imm_binary, 2) + 1)
            else:
                self.imm = int(self.instruction[16:], 2)


        else:
            print("Unsupported instruction:", self.instruction)

    def EX(self): #this method performs the EX stage - operation between operator and operands
        if self.opcode == '000000': #checking the opcode on a case by case basis
            funct = self.instruction[-6:]
            if funct == '100000':  # add
                self.result = self.registers[self.rs] + self.registers[self.rt]
            elif funct == '100010':  # sub
                self.result = self.registers[self.rs] - self.registers[self.rt]
            elif funct == '101010':  # slt
                self.result = 1 if self.registers[self.rs] < self.registers[self.rt] else 0
        
        elif self.opcode=='011100': #mul
            self.result = self.registers[self.rs] * self.registers[self.rt]

        elif self.opcode == '100011': # lw
            self.address = (self.registers[self.rs] + self.imm)
        
        elif self.opcode == '101011': #sw
            self.address = (self.registers[self.rs] + self.imm)
        
        elif self.opcode == '001000': # addi
            self.result = self.registers[self.rs] + self.imm

        elif self.opcode== '000010':#jump
            self.jump_address=int(self.instruction[6:],2)
            self.pc=self.jump_address-1048576-1

        elif self.opcode=='000100':#beq
            self.result = self.registers[self.rs]==self.registers[self.rt]    
            if(self.result == True):     
                self.pc=self.pc+self.imm

        elif self.opcode=='000101':#bne
            self.result = self.registers[self.rs]!=self.registers[self.rt]
            if(self.result == True):     
                self.pc=self.pc+self.imm

        else:
            print("Unsupported instruction:", self.instruction)
    
    def MEM(self): #this method writes down the data in the corresponding memory location
        if self.opcode == '100011': # lw
            self.result = self.memory[self.address]
        
        elif self.opcode == '101011': #sw
            self.memory[self.address] = self.registers[self.rt]
    
    def WB(self): #this method writes down the data in the corresponding registers
        if self.opcode == '000000': #checking the opcode on a case by case basis
            funct = self.instruction[-6:]
            if funct == '100000':  # add
                self.registers[self.rd] = self.registers[self.rs] + self.registers[self.rt]
            elif funct == '100010':  # sub
                self.registers[self.rd] = self.registers[self.rs] - self.registers[self.rt]
            elif funct == '101010':  # slt
                self.registers[self.rd] = 1 if self.registers[self.rs] < self.registers[self.rt] else 0
            
        elif self.opcode=='011100': #mul
            self.registers[self.rd] = self.result 

        elif self.opcode == '100011': # lw
            self.registers[self.rt] = self.result
        
        elif self.opcode == '101011': #sw
                pass
        elif self.opcode == '001000': # addi
            self.registers[self.rt] = self.registers[self.rs] + self.imm

        elif self.opcode== '000010':#jump
                pass
        elif self.opcode=='000100' or self.opcode=='000101':#beq and bne
            pass

        else:
            print("Unsupported instruction:", self.instruction)

    def run_program(self,machine_code):#this method runs the program
        self.pc = 0
        while(self.pc<len(machine_code)):#running through input code 
            self.IF(machine_code)
            self.ID()
            self.EX()
            self.MEM()
            self.WB()
            self.pc+=1#incrementing the pc by 1
    
        
with open('IMT2022570_IMT2022576_Sort.txt', 'r') as file: #opening the input file which has a machine code for a single program 
    machine_code = [line.strip() for line in file.readlines()]



processor = MIPSProcessor() #creating an instance of the MIPSProcessor Class
processor.run_program(machine_code) #running the program

 #printing the final values of registers 
for i, value in enumerate(processor.registers):
    print(f"register - {i}: {value}")
 #printing the final values of all memory locations
for i in range(0,len(processor.memory),4):
    print(f"memory - {i}: {processor.memory[i]}")

print(f"pc is {processor.pc*4}") #printing the final value of PC
print(f"no.of clock cycles taken is {processor.clock_cycles*5}") #printing the final value of number of clock cycles