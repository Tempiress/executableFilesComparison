import requests
from bs4 import BeautifulSoup
url = 'https://docs.oracle.com/cd/E18752_01/html/817-5477/ennbz.html#eoizm'
response = requests.get(url)
html_content = response.text

soup = BeautifulSoup(html_content, 'html.parser')
tr_headings = soup.find_all('tt')

for i in tr_headings:
    if i.text.isupper():
       a = 3
       #print(i.text)


dir = ["abc", "das"]


DTI = ["BSWAP","CBW","CDQ","CDQE","CMOVA","CMOVAE","CMOVB","CMOVBE","CMOVC","CMOVE","CMOVG","CMOVGE","CMOVL","COMVLE","CMOVNA","CMOVNAE","CMOVNB","CMOVNBE","CMOVNC","CMOVNE","CMOVNG","CMOVNGE","CMOVNL","CMOVNLE","CMOVNO","CMOVNP","CMOVNS","CMOVNZ","CMOVO","CMOVP","CMOVPE","CMOVPO","CMOVS","CMOVZ","CMPXCHG","CMPXCHG8B","CQO","CQO","CWD","CWDE","MOV","MOVABS","MOVABS","AL","AX","GAX","RAX","MOVSX","MOVZX","POP","POPA","POPAD","PUSH","PUSHA","PUSHAD","XADD","XCHG"]
BAI = ["ADC","ADD","CMP","DEC","DIV","IDIV","IMUL","INC","MUL","NEG","SBB","SUB"]
DAI = ["AAA","AAD","AAM","AAS","DAA","DAS"]
LI = ["AND","NOT","OR","XOR"]
SRI = ["RCL","RCR","ROL","ROR","SAL","SAR","SHL","SHLD","SHR","SHRD"]
BBI = ["BSF","BSR","BT","BTC","BTR","BTS","SETA","SETAE","SETB","SETBE","SETC","SETE","SETG","SETGE","SETL","SETLE","SETNA","SETNAE","SETNB","SETNBE","SETNC","SETNE","SETNG","SETNGE","SETNL","SETNLE","SETNO","SETNP","SETNS","SETNZ","SETO","SETP","SETPE","SETPO","SETS","SETZ","TEST"]
CTI = ["BOUND","CALL","ENTER","INT","INTO","IRET","JA","JAE","JB","JBE","JC","JCXZ","JE","JECXZ","JG","JGE","JL","JLE","JMP","JNAE","JNB","JNBE","JNC","JNE","JNG","JNGE","JNL","JNLE","JNO","JNP","JNS","JNZ","JO","JP","JPE","JPO","JS","JZ","CALL","LEAVE","LOOP","LOOPE","LOOPNE","LOOPNZ","LOOPZ","RET"]
SI = ["CMPS","CMPSB","CMPSD","CMPSW","LODS","LODSB","LODSD","LODSW","MOVS","MOVSB","MOVSD","MOVSW","REP","REPNE","REPNZ","REPE","REPZ","SCAS","SCASB","SCASD","SCASW","STOS","STOSB","STOSD","STOSW"]
IOI = ["IN","INS","INSB","INSD","INSW","OUT","OUTS","OUTSB","OUTSD","OUTSW"]
FCI = ["CLC","CLD","CLI","CMC","LAHF","POPF","POPFL","PUSHF","PUSHFL","SAHF","STC","STD","STI"]
SRI = ["LDS","LES","LFS","LGS","LSS"]
MLI = ["CPUID","LEA","NOP","UD2","XLAT","XLATB"]


r = ""
with open("lexems.txt", "r") as f:
    a = f.readlines()
    for e in a:
        #r = r + "," +  e + "\"" + ","
        r = r + "," + " " + "\"" + e + "\""

r = r.replace(' ', '')
r = r.replace('\n', '')
print(r)


# Data Transfer Instructions
#
# BSWAP
# CBW
# CDQ
# CDQE
# CMOVA
# CMOVAE
# CMOVB
# CMOVBE
# CMOVC
# CMOVE
# CMOVG
# CMOVGE
# CMOVL
# COMVLE
# CMOVNA
# CMOVNAE
# CMOVNB
# CMOVNBE
# CMOVNC
# CMOVNE
# CMOVNG
# CMOVNGE
# CMOVNL
# CMOVNLE
# CMOVNO
# CMOVNP
# CMOVNS
# CMOVNZ
# CMOVO
# CMOVP
# CMOVPE
# CMOVPO
# CMOVS
# CMOVZ
# CMPXCHG
# CMPXCHG8B
# CQO
# CQO
# CWD
# CWDE
# MOV
# MOVABS
# MOVABS
# AL
# AX
# GAX
# RAX
# MOVSX
# MOVZX
# POP
# POPA
# POPAD
# PUSH
# PUSHA
# PUSHAD
# XADD
# XCHG
#
# Binary Arithmetic Instructions  ----
#
# ADC
# ADD
# CMP
# DEC
# DIV
# IDIV
# IMUL
# INC
# MUL
# NEG
# SBB
# SUB
#
# Decimal Arithmetic Instructions ---
#
# AAA
# AAD
# AAM
# AAS
# DAA
# DAS
#
# Logical Instructions --
#
# AND
# NOT
# OR
# XOR
#
# Shift and Rotate Instructions ---
#
# RCL
# RCR
# ROL
# ROR
# SAL
# SAR
# SHL
# SHLD
# SHR
# SHRD
#
# Bit and Byte Instructions ---
#
# BSF
# BSR
# BT
# BTC
# BTR
# BTS
# SETA
# SETAE
# SETB
# SETBE
# SETC
# SETE
# SETG
# SETGE
# SETL
# SETLE
# SETNA
# SETNAE
# SETNB
# SETNBE
# SETNC
# SETNE
# SETNG
# SETNGE
# SETNL
# SETNLE
# SETNO
# SETNP
# SETNS
# SETNZ
# SETO
# SETP
# SETPE
# SETPO
# SETS
# SETZ
# TEST
#
# Control Transfer Instructions -----
#
# BOUND
# CALL
# ENTER
# INT
# INTO
# IRET
# JA
# JAE
# JB
# JBE
# JC
# JCXZ
# JE
# JECXZ
# JG
# JGE
# JL
# JLE
# JMP
# JNAE
# JNB
# JNBE
# JNC
# JNE
# JNG
# JNGE
# JNL
# JNLE
# JNO
# JNP
# JNS
# JNZ
# JO
# JP
# JPE
# JPO
# JS
# JZ
# CALL
# LEAVE
# LOOP
# LOOPE
# LOOPNE
# LOOPNZ
# LOOPZ
# RET
#
# String Instructions ---
#
#
# CMPS
# CMPSB
# CMPSD
# CMPSW
# LODS
# LODSB
# LODSD
# LODSW
# MOVS
# MOVSB
# MOVSD
# MOVSW
# REP
# REPNE
# REPNZ
# REPE
# REPZ
# SCAS
# SCASB
# SCASD
# SCASW
# STOS
# STOSB
# STOSD
# STOSW
#
# I/O Instructions ----------
#
# IN
# INS
# INSB
# INSD
# INSW
# OUT
# OUTS
# OUTSB
# OUTSD
# OUTSW
#
# Flag Control (EFLAG) Instructions  ----------
#
# CLC
# CLD
# CLI
# CMC
# LAHF
# POPF
# POPFL
# PUSHF
# PUSHFL
# SAHF
# STC
# STD
# STI
#
# Segment Register Instructions --------
#
# LDS
# LES
# LFS
# LGS
# LSS
#
# Miscellaneous Instructions ---------
#
# CPUID
# LEA
# NOP
# UD2
# XLAT
# XLATB

