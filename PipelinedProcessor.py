class PipelinedMIPSProcessor:
    def __init__(self, machine_code):
        # Initialize processor state
        self.registers = [0] * 32
        self.memory = [0] * 100
        self.pc = 0
        self.clock_cycles = 0
        self.machine_code = machine_code
        # t1-9 t2-10 s2-18 s4-20
        #t1,t2,t3 t1(n)=5 t2(input)=0 t3(output)=10
        # Set initial values for some registers and memory locations
        self.registers[9]=5  # t1=n=5
        self.registers[10]=0 #t2=0
        self.registers[11]=24 #t3=24
        self.memory[0]=5
        self.memory[4]=7
        self.memory[8]=6
        self.memory[12]=2
        self.memory[16]=4
        # Initialize IF/ID with the first instruction and remaining with None
        self.pipeline_registers = {'IF/ID': {'instruction': self.fetch_instruction(), 'pc': 1,'num_stall':0},
                                   'ID/EX': None ,
                                   'EX/MEM':None ,
                                   'MEM/WB': None }
        self.pipeline_write_back={'WB':None}

    def fetch_instruction(self):
        # Fetch the next instruction from the machine code using pc as index
        if self.pc < len(self.machine_code):
            instruction = self.machine_code[self.pc]
            self.pc += 1
            return instruction
        else:
            return None

    def instruction_fetch(self):
        # Fetch the next instruction and update the IF/ID pipeline register
        instruction = self.fetch_instruction()
        if instruction is not None:
            self.pipeline_registers['IF/ID'] = {'instruction': instruction, 'pc': self.pc,'num_stall':0}
        else:
            # If there are no more instructions, set the pipeline register to None
            self.pipeline_registers['IF/ID'] = None

    def instruction_decode(self):
        # Decode the instruction and update the ID/EX pipeline register
        if_stage = self.pipeline_registers['IF/ID']
        instruction = if_stage.get('instruction')
        if instruction:
            opcode = instruction[:6]
             # Decode different instruction types
            if opcode == '000000': # R-type
                funct = instruction[-6:]
                self.pipeline_registers['ID/EX'] = {'opcode': opcode, 'funct': funct,
                                                                       'reg1': self.registers[int(instruction[6:11], 2)],
                                                                       'reg2': self.registers[int(instruction[11:16], 2)],
                                                                       'pc': if_stage['pc'] ,
                                                                       'reg_dst': int(instruction[16:21], 2),
                                                                       'read_reg_1':int(instruction[6:11], 2),
                                                                       'read_reg_2':int(instruction[11:16], 2)
                                                                       }
            elif opcode=='011100': # mul
                self.pipeline_registers['ID/EX'] = {'opcode': opcode, 
                                                                       'reg1': self.registers[int(instruction[6:11], 2)],
                                                                       'reg2': self.registers[int(instruction[11:16], 2)],
                                                                       'pc': if_stage['pc'] ,
                                                                       'reg_dst': int(instruction[16:21], 2),
                                                                       'read_reg_1':int(instruction[6:11], 2),
                                                                       'read_reg_2':int(instruction[11:16], 2)
                                                                       }
            elif opcode == '100011' or opcode == '101011' or opcode == '001000' or opcode == '000100' or opcode=='000101': # I - type
                self.pipeline_registers['ID/EX'] = {'opcode': opcode,
                                                                       'reg1': self.registers[int(instruction[6:11], 2)],
                                                                       'pc': if_stage['pc'] ,
                                                                       'imm': int(instruction[16:], 2),
                                                                       'reg_dst': int(instruction[11:16], 2),
                                                                       'read_reg_1':int(instruction[6:11], 2)

                                                                       }
            elif opcode == '000010': # Jump
                self.pipeline_registers['ID/EX'] = {'opcode': opcode,
                                                                       'jump_target': int(instruction[6:], 2),'reg_dst':None,'pc': if_stage['pc']}
                self.pc=self.pipeline_registers['ID/EX'].get('jump_target')-1048576
                
            if opcode=='001000' or opcode=='000100' or opcode=='000101': # if imm is negative for addi or beq or bne
                if(instruction[16]=='1'):
                    # 2's complement
                    imm_binary = ''.join('1' if bit == '0' else '0' for bit in instruction[16:])
                    imm = -(int(imm_binary, 2) + 1)
                    
                    self.pipeline_registers['ID/EX'].update({'imm':imm})

            # forward in id-stage from  execute and  mem_access stages for beq and bne instructions 
            if opcode=='000100' or opcode=='000101':
                self.pipeline_registers['ID/EX'].update({'reg2':self.registers[int(instruction[11:16], 2)],'reg_dst':None,'read_reg_2':int(instruction[11:16], 2) })
                id_pip=self.pipeline_registers['ID/EX']
                
                
                for stage in ['MEM/WB','EX/MEM']:
                    if self.pipeline_registers[stage] is not None and self.pipeline_registers[stage].get('result') is not None:
                        if id_pip.get('read_reg_1') is not None and id_pip.get('read_reg_1') == self.pipeline_registers[stage].get('reg_dst',-1):
                    
                            self.pipeline_registers['ID/EX'].update({'reg1' : self.pipeline_registers[stage].get('result')})
                        if id_pip.get('read_reg_2') is not None and id_pip.get('read_reg_2') == self.pipeline_registers[stage].get('reg_dst',-1):
                            self.pipeline_registers['ID/EX'].update({'reg2' : self.pipeline_registers[stage].get('result')})

                # fast branching in beq            
                if(opcode=='000100'):#beq
                    if id_pip.get('reg1') == id_pip.get('reg2'):
                        self.pc=id_pip.get('pc')+ id_pip.get('imm')
                        if(self.pc==len(self.machine_code)):
                            # self.pc+=1
                            # empty the pipeline register when you reached the end of machine codes
                            self.pipeline_registers['IF/ID']=None
                            self.pipeline_registers['ID/EX']=None
                            self.pipeline_registers['EX/MEM']=None
                            self.pipeline_registers['MEM/WB']=None
                        
                # fast branching in bne        
                if(opcode=='000101'):#bne
                    if id_pip.get('reg1') != id_pip.get('reg2'):
                        self.pc=id_pip.get('pc')+ id_pip.get('imm')
                        if(self.pc==len(self.machine_code)):
                            # self.pc+=1
                            # empty the pipeline register when you reached the end of machine codes
                            self.pipeline_registers['IF/ID']=None
                            self.pipeline_registers['ID/EX']=None
                            self.pipeline_registers['EX/MEM']=None
                            self.pipeline_registers['MEM/WB']=None
                        
                        

        if if_stage.get('pc')>=len(self.machine_code):
            self.pipeline_registers['IF/ID']=None

    def execute_instruction(self):
        # perform ex_stage  using alu and update the 'EX/MEM' register 
        id_pip = self.pipeline_registers['ID/EX']
        opcode = id_pip.get('opcode')
        reg_dst=id_pip.get('reg_dst')
        pc=id_pip.get('pc')
       
        # handling hazards by forwarding from write_back stage
        store_word_flag=0

        if self.pipeline_write_back is not None and self.pipeline_write_back.get('result') is not None:
            if id_pip.get('read_reg_1') is not None and id_pip.get('read_reg_1') == self.pipeline_write_back.get('reg_dst',-1):
                    self.pipeline_registers['ID/EX'].update({'reg1' : self.pipeline_write_back.get('result')})
            if id_pip.get('read_reg_2') is not None and id_pip.get('read_reg_2') == self.pipeline_write_back.get('reg_dst',-1):
                    self.pipeline_registers['ID/EX'].update({'reg2' : self.pipeline_write_back.get('result')})
        if self.pipeline_write_back is not None and self.pipeline_write_back.get('value') is not None:
            if id_pip.get('read_reg_1') is not None and id_pip.get('read_reg_1') == self.pipeline_write_back.get('reg_dst',-1):
                    self.pipeline_registers['ID/EX'].update({'reg1' : self.pipeline_write_back.get('value')})
                    
            if id_pip.get('read_reg_2') is not None and id_pip.get('read_reg_2') == self.pipeline_write_back.get('reg_dst',-1):
                    self.pipeline_registers['ID/EX'].update({'reg2' : self.pipeline_write_back.get('value')})
            # Handle specific case for store word instruction        
            if opcode=='101011':
                    if id_pip.get('reg_dst') is not None and id_pip.get('reg_dst') == self.pipeline_write_back.get('reg_dst',-1):
                        
                        store_word_flag=1
                        data=self.pipeline_write_back.get('value')


        # handling hazards by forwarding from mem_access  stage        
        stage='MEM/WB'
        if self.pipeline_registers[stage] is not None and self.pipeline_registers[stage].get('result') is not None:
            if id_pip.get('read_reg_1') is not None and id_pip.get('read_reg_1') == self.pipeline_registers[stage].get('reg_dst',-1):
                self.pipeline_registers['ID/EX'].update({'reg1' : self.pipeline_registers[stage].get('result')})
                
            if id_pip.get('read_reg_2') is not None and id_pip.get('read_reg_2') == self.pipeline_registers[stage].get('reg_dst',-1):
                self.pipeline_registers['ID/EX'].update({'reg2' : self.pipeline_registers[stage].get('result')})
            
        if self.pipeline_registers[stage] is not None and self.pipeline_registers[stage].get('value') is not None:
            if id_pip.get('read_reg_1') is not None and id_pip.get('read_reg_1') == self.pipeline_registers[stage].get('reg_dst',-1):
                self.pipeline_registers['ID/EX'].update({'reg1' : self.pipeline_registers[stage].get('value')})
                
            if id_pip.get('read_reg_2') is not None and id_pip.get('read_reg_2') == self.pipeline_registers[stage].get('reg_dst',-1):
                self.pipeline_registers['ID/EX'].update({'reg2' : self.pipeline_registers[stage].get('value')})
            # Handle specific case for store word instruction    
            if opcode=='101011':
                if id_pip.get('reg_dst') is not None and id_pip.get('reg_dst') == self.pipeline_registers[stage].get('reg_dst',-1):  
                    store_word_flag=1
                    data=self.pipeline_registers[stage].get('value')
                        

        id_pip = self.pipeline_registers['ID/EX']
        if id_pip:
            # Execute different instruction types
            if opcode == '000000':
                funct = id_pip.get('funct')
                if funct == '100000':  # add
                    result = id_pip.get('reg1') + id_pip.get('reg2')
                    self.pipeline_registers['EX/MEM'] = {'result': result}
                elif funct == '100010':  # sub
                    result = id_pip.get('reg1') - id_pip.get('reg2')
                    self.pipeline_registers['EX/MEM'] = {'result': result}
                elif funct == '011000':  # mult
                    result = id_pip.get('reg1') * id_pip.get('reg2')
                    self.pipeline_registers['EX/MEM'] = {'result': result}
                elif funct == '101010':  # slt
                    result = 1 if id_pip.get('reg1') < id_pip.get('reg2') else 0
                    
                    self.pipeline_registers['EX/MEM'] = {'result': result}
            elif opcode == '011100':  # mul
                result = id_pip.get('reg1') * id_pip.get('reg2')
                self.pipeline_registers['EX/MEM'] = {'result': result}
            elif opcode == '100011':  # lw 
                address = id_pip.get('reg1') + id_pip.get('imm')
                self.pipeline_registers['EX/MEM'] = {'address': address}
            elif opcode == '101011':  # sw
                address = id_pip.get('reg1') + id_pip.get('imm')
                data_to_store = self.registers[id_pip.get('reg_dst')]
                self.pipeline_registers['EX/MEM'] = {'address': address, 'data_to_store': data_to_store,'imm':id_pip.get('imm')}
                if(store_word_flag==1):
                    self.pipeline_registers['EX/MEM'].update({'data_to_store':data})
            elif opcode == '001000':  # addi
                result = id_pip.get('reg1') + id_pip.get('imm')
                self.pipeline_registers['EX/MEM'] = {'result': result}
                
            elif opcode == '000010':  # jump
                target = id_pip.get('jump_target')
                self.pipeline_registers['EX/MEM'] = {'jump_target': target}
            elif opcode == '000100' or opcode=='000101':  # beq
                self.pipeline_registers['EX/MEM']=({'pc':pc}) 
            
            else:
                print("Unsupported instruction:", opcode)
        if self.pipeline_registers['EX/MEM'] is not None :        
            self.pipeline_registers['EX/MEM'].update({'opcode':opcode})        
            self.pipeline_registers['EX/MEM'].update({'reg_dst':reg_dst})   
            self.pipeline_registers['EX/MEM'].update({'pc':pc})   

        if id_pip.get('pc')>=len(self.machine_code):
            self.pipeline_registers['ID/EX']=None        

    def memory_access(self):
        # Fetch data from the EX/MEM pipeline register and update the MEM/WB pipeline accordingly
        ex_stage = self.pipeline_registers['EX/MEM']
        reg_dst=ex_stage.get('reg_dst')
        result=ex_stage.get('result')
        pc=ex_stage.get('pc')
        opcode = ex_stage.get('opcode')
        stage='MEM/WB'
        
        # Handling data forwarding from the write_back stage

        if self.pipeline_write_back is not None and self.pipeline_write_back.get('result') is not None:
                if ex_stage.get('data_to_store') is not None and ex_stage.get('reg_dst') == self.pipeline_write_back.get('reg_dst',-1):
                    self.pipeline_registers['EX/MEM'].update({'data_to_store' : self.pipeline_write_back.get('result')})
        if self.pipeline_write_back is not None and self.pipeline_write_back.get('value') is not None:          
                if ex_stage.get('data_to_store') is not None and ex_stage.get('reg_dst') == self.pipeline_write_back.get('reg_dst',-1):
                    self.pipeline_registers['EX/MEM'].update({'data_to_store' : self.pipeline_write_back.get('value')})

        # Handling data forwarding from the mem_access stage
        if self.pipeline_registers[stage] is not None and self.pipeline_registers[stage].get('result') is not None:
                if ex_stage.get('data_to_store') is not None and ex_stage.get('reg_dst') == self.pipeline_registers[stage].get('reg_dst',-1):
                    self.pipeline_registers['EX/MEM'].update({'data_to_store' : self.pipeline_registers[stage].get('result')})
                    
        if self.pipeline_registers[stage] is not None and self.pipeline_registers[stage].get('value') is not None:            
                if ex_stage.get('data_to_store') is not None and ex_stage.get('reg_dst') == self.pipeline_registers[stage].get('reg_dst',-1):
                    self.pipeline_registers['EX/MEM'].update({'data_to_store' : self.pipeline_registers[stage].get('value')})
                    
        # Access memory for lw and sw  in the memory_access stage
        ex_stage = self.pipeline_registers['EX/MEM']            
        if ex_stage:
            if opcode == '100011':  # lw
                self.pipeline_registers['MEM/WB'] = {'value': self.memory[ex_stage.get('address')],'pc':ex_stage.get('pc')}
            elif opcode == '101011':  # sw
                self.memory[ex_stage.get('address')] = ex_stage.get('data_to_store')
                self.pipeline_registers['MEM/WB'] = {'pc':ex_stage.get('pc')}
                
                
            else:
                self.pipeline_registers['MEM/WB'] = {'pc':ex_stage.get('pc')}
                   
        if self.pipeline_registers['MEM/WB'] is not None:
            self.pipeline_registers['MEM/WB'].update({'reg_dst':reg_dst})
            self.pipeline_registers['MEM/WB'].update({'result':result})
           
            self.pipeline_registers['MEM/WB'].update({'opcode':opcode})

        if ex_stage.get('pc')>=len(self.machine_code):
            self.pipeline_registers['EX/MEM']=None        

    def write_back(self):
        # Fetch data from the MEM/WB pipeline register and update the register file accordingly
        mem_stage = self.pipeline_registers['MEM/WB']
        self.pipeline_write_back=mem_stage.copy()
        if mem_stage:
            opcode = mem_stage.get('opcode')
            if opcode == '000000':  # r-type
                self.registers[mem_stage.get('reg_dst')] = mem_stage.get('result')
            elif opcode == '100011':  # lw
                self.registers[mem_stage.get('reg_dst')] = mem_stage.get('value')
            elif opcode == '001000' or opcode == '011100':  # addi, mul
                self.registers[mem_stage.get('reg_dst')] = mem_stage.get('result')
               
        if mem_stage.get('pc')>=len(self.machine_code):        
            
            self.pipeline_registers['MEM/WB']= None       

    def execute_instruction_set(self):
        # Execute stages for each instruction in the set
            for stage in reversed(self.pipeline_registers):
                if self.pipeline_registers[stage] is not None:
                    # keeping stalls if there is a hazard with lw
                    if stage=='IF/ID':
                        ind=list(self.pipeline_registers).index(stage)
                        instruction=self.pipeline_registers[stage].get('instruction')
                        opcode=instruction[:6]
                        num_stall=self.pipeline_registers[stage].get('num_stall')
                        if opcode == '000000' or opcode=='011100': #r-format
                            rs=int(instruction[6:11], 2)
                            rt=int(instruction[11:16], 2)
                        if opcode == '000010':#jump
                            rs=None
                            rt=None
                        if opcode == '100011' or opcode == '101011' or opcode == '001000' or opcode == '000100' or opcode=='000101':
                            rs= int(instruction[6:11], 2)
                            rt=None 
                        for stage_check in list(self.pipeline_registers)[ind+1:] :
                            if self.pipeline_registers[stage_check] is not None and self.pipeline_registers[stage] is not None:
                                if num_stall<1:
                                    if rs is not None:
                                        if self.pipeline_registers[stage_check].get('reg_dst') is not None and (self.pipeline_registers[stage_check].get('reg_dst')== rs or self.pipeline_registers[stage_check].get('reg_dst')==rt):
                                            if(self.pipeline_registers[stage_check]=='100011'):#hazard with lw
                                                self.pipeline_registers[stage].update({'num_stall':num_stall+1}) 
                                                return 
                                    if rt is not None:
                                        if self.pipeline_registers[stage_check].get('value') is not None and  (self.pipeline_registers[stage_check].get('value')== rs or self.pipeline_registers[stage_check].get('value')== rt):
                                            if(self.pipeline_registers[stage_check]=='100011'):#hazard with lw
                                                self.pipeline_registers[stage].update({'num_stall':num_stall+1}) 
                                                return 
                                    if opcode == '101011':
                                        reg_dst=int(instruction[11:16], 2)
                                        if reg_dst is not None:
                                             if self.pipeline_registers[stage_check].get('reg_dst') is not None and self.pipeline_registers[stage_check].get('reg_dst')== reg_dst:
                                                 if(self.pipeline_registers[stage_check]=='100011'):#hazard with lw
                                                    self.pipeline_registers[stage].update({'num_stall':num_stall+1}) 
                                                    return
                                             if self.pipeline_registers[stage_check].get('value') is not None and self.pipeline_registers[stage_check].get('value')== reg_dst:
                                                 if(self.pipeline_registers[stage_check]=='100011'):#hazard with lw
                                                    self.pipeline_registers[stage].update({'num_stall':num_stall+1}) 
                                                    return
                    #  # ########
                    self.execute_stage(stage)
                    
                    

    def execute_stage(self, stage):
        # Execute the specified stage for the instruction at the given index
        if stage == 'IF/ID':
            self.instruction_decode()
            self.instruction_fetch()
        elif stage == 'ID/EX':
            self.execute_instruction()
        elif stage == 'EX/MEM':
            self.memory_access()
        elif stage == 'MEM/WB':
            self.write_back()

    def run_program(self):
        while self.pc < len(self.machine_code) or any(stage is not  None for stage in self.pipeline_registers.values()):
            # Execute stages for each instruction in a set
            self.execute_instruction_set()
            self.clock_cycles += 1


# Example usage:
# Load machine code from the output file generated by the assembler
with open('IMT2022570_IMT2022576_Sort.txt', 'r') as file:
    machine_code = [line.strip() for line in file.readlines()]

processor = PipelinedMIPSProcessor(machine_code)
processor.run_program()

# Print the final register values
for i, value in enumerate(processor.registers):
    print(f"register - {i}: {value}")
# processor.pc-=1

for i in range(0, len(processor.memory), 4):
    print(f"memory - {i}: {processor.memory[i]}")
print(f"pc is {processor.pc*4}")
print(f"no. of clock cycles taken is {processor.clock_cycles+1}")
