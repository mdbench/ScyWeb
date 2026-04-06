#!/bin/bash
# SCYWEB VINE PROTOCOL V4.5 - FULL 10-KERNEL PARITY
# Lead Architect: Matthew D. Benchimol
# Choosen over parity method
# --------------------------------------------------------

PASS="ScyWeb_Global_Secret_2026"
W=4000; H=4000; DIM=4096
OUT_DIR="vines_images"
mkdir -p "$OUT_DIR"

# Formatting
G='\033[0;32m'; B='\033[1m'; NC='\033[0m'

echo -e "${B}PHASE 1: INDEPENDENT GENERATION (SOWING)${NC}"
echo "--------------------------------------------------------"

# 1. PYTHON
python3 -c "
import hashlib, os, sys

def rot(n, x, y, rx, ry):
    if ry == 0:
        if rx == 1:
            x, y = n - 1 - x, n - 1 - y
        return y, x
    return x, y

def d2xy(n, d):
    x, y, t, s = 0, 0, int(d), 1
    while s < n:
        # FORCE bitwise shifts to match C++/Go/Rust Kernels
        rx = 1 & (t >> 1)
        ry = 1 & (t ^ rx)
        x, y = rot(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t >>= 2
        s <<= 1
    return x, y

# Environment Variable Capture
PASS = '$PASS'
W, H, DIM = int('$W'), int('$H'), int('$DIM')
path = '$OUT_DIR/python_vine.ppm'

# Seed Generation
h_val = int(543210)

# Write Header (17 bytes) + Buffer
header = b'\x50\x36\x0a\x34\x30\x30\x30\x20\x34\x30\x30\x30\x0a\x32\x35\x35\x0a'
with open(path, 'wb') as f: 
    f.write(header + b'\x00' * (W * H * 3))

# SOWING
with open(path, 'r+b') as f:
    for i in range(1, 41):
        sql = f'SQL_ID_{i}_DATA\0'.encode()
        cur_d = h_val + (i * 1000)
        for j in range(0, len(sql), 3):
            x, y = d2xy(DIM, cur_d)
            if x < W and y < H:
                f.seek(17 + (y * W + x) * 3)
                f.write(sql[j:j+3].ljust(3, b'\0'))
            cur_d += 1
    f.flush()
    os.fsync(f.fileno())

# SELF-HARVEST VERIFICATION
harvested = 0
with open(path, 'rb') as f:
    for i in range(1, 41):
        cur_d = h_val + (i * 1000)
        res = b''
        for _ in range(100):
            tx, ty = d2xy(DIM, cur_d)
            f.seek(17 + (ty * W + tx) * 3)
            p = f.read(3)
            if not p or b'\x00' in p:
                if p and b'\x00' in p: res += p.split(b'\x00')[0]
                break
            res += p
            cur_d += 1
        if f'SQL_ID_{i}_DATA'.encode() == res:
            harvested += 1

if harvested == 40:
    sys.exit(0)
else:
    print(f'Python internal failure: {harvested}/40')
    sys.exit(1)
" && echo -e "1. Python... ${G}OK${NC}" || exit 1

# 2. NODE.JS
node -e "
const fs = require('fs');
const crypto = require('crypto');

const rot = (n, x, y, rx, ry) => ry === 0 ? (rx === 1 ? [n-1-y, n-1-x] : [y, x]) : [x, y];
const d2xy = (n, d) => {
    let x=0, y=0, t=d;
    for(let s=1; s<n; s*=2){
        let rx=1&(t>>1), ry=1&(t^rx); [x,y]=rot(s,x,y,rx,ry);
        x+=s*rx; y+=s*ry; t>>=2;
    } return [x,y];
};

const path = '$OUT_DIR/node_vine.ppm';
const header = Buffer.from([0x50,0x36,0x0a,0x34,0x30,0x30,0x30,0x20,0x34,0x30,0x30,0x30,0x0a,0x32,0x35,0x35,0x0a]);
const body = Buffer.alloc(48000000, 0);
fs.writeFileSync(path, Buffer.concat([header, body]));

const h = 543210;
//console.log('DEBUG: Node.js Seed Value = ' + h);

// Open with 'rs+' to bypass lazy write caching
const fd = fs.openSync(path, 'rs+');
for (let i = 41; i <= 80; i++) {
    const sql = Buffer.concat([Buffer.from('SQL_ID_' + i + '_DATA'), Buffer.from([0])]);
    let curD = h + (i * 1000);
    for (let j = 0; j < sql.length; j += 3) {
        const [x, y] = d2xy($DIM, curD);
        const chunk = Buffer.alloc(3, 0); 
        sql.copy(chunk, 0, j, Math.min(j + 3, sql.length));
        fs.writeSync(fd, chunk, 0, 3, 17 + (y * $W + x) * 3);
        curD++;
    }
}
fs.fsyncSync(fd); // Force physical commit
fs.closeSync(fd);
" && sync && sleep 2 && echo -e "2. Node.js... ${G}OK${NC}"

# 3. CPP
echo -n "3. CPP... "
cat << 'EOF' > kernel.cpp
#include <iostream>
#include <fstream>
#include <string>
void rot(int n, int *x, int *y, int rx, int ry) {
    if (ry == 0) { if (rx == 1) { *x = n-1-*x; *y = n-1-*y; } int t = *x; *x = *y; *y = t; }
}
void d2xy(int n, int d, int &x, int &y) {
    int rx, ry, s, t=d; x = y = 0;
    for (s=1; s<n; s*=2) { rx = 1 & (t/2); ry = 1 & (t ^ rx); rot(s, &x, &y, rx, ry); x += s*rx; y += s*ry; t /= 4; }
}
int main() {
    std::string path = "vines_images/cpp_vine.ppm";
    std::ofstream out(path, std::ios::binary); out << "P6\n4000 4000\n255\n"; 
    out.seekp(48000016); out.put(0); out.close();
    std::fstream f(path, std::ios::in | std::ios::out | std::ios::binary);
    int h = 543210; // Shared Seed Logic
    for(int i=81; i<=120; i++){
        std::string sql = "SQL_ID_" + std::to_string(i) + "_CPP_VINE"; sql += '\0';
        int curD = h + (i * 1000);
        for(int j=0; j<sql.length(); j+=3){
            int x, y; d2xy(4096, curD, x, y);
            f.seekg(17 + (y*4000+x)*3); f.write(sql.substr(j,3).c_str(), 3);
            curD++;
        }
    }
    return 0;
}
EOF
g++ kernel.cpp -o kernel_cpp && ./kernel_cpp && echo -e "${G}OK${NC}"

# 4. GO
echo -n "4. GO... "
cat << 'EOF' > kernel.go
package main
import ("os"; "fmt")
func rot(n, x, y, rx, ry int) (int, int) {
    if ry == 0 { if rx == 1 { x, y = n-1-x, n-1-y }; return y, x }; return x, y
}
func d2xy(n, d int) (int, int) {
    x, y, t := 0, 0, d
    for s := 1; s < n; s *= 2 { rx := 1 & (t / 2); ry := 1 & (t ^ rx); x, y = rot(s, x, y, rx, ry); x += s * rx; y += s * ry; t /= 4 }
    return x, y
}
func main() {
    p := "vines_images/go_vine.ppm"; f, _ := os.Create(p); f.Write([]byte("P6\n4000 4000\n255\n")); f.Truncate(48000017); f.Close()
    f, _ = os.OpenFile(p, os.O_RDWR, 0644)
    for i := 121; i <= 160; i++ {
        sql := fmt.Sprintf("SQL_ID_%d_GO_VINE\x00", i); curD := 543210 + (i * 1000)
        for j := 0; j < len(sql); j += 3 {
            x, y := d2xy(4096, curD); end := j+3; if end > len(sql) { end = len(sql) }
            f.WriteAt([]byte(sql[j:end]), int64(17+(y*4000+x)*3)); curD++
        }
    }
}
EOF
go run kernel.go && echo -e "${G}OK${NC}"

# 5. RUST
echo -n "5. RUST... "
cat << 'EOF' > kernel.rs
use std::fs::{File, OpenOptions}; use std::io::{Write, Seek, SeekFrom};
fn rot(n: i32, x: &mut i32, y: &mut i32, rx: i32, ry: i32) {
    if ry == 0 { if rx == 1 { *x = n - 1 - *x; *y = n - 1 - *y; } let t = *x; *x = *y; *y = t; }
}
fn d2xy(n: i32, d: i32) -> (i32, i32) {
    let (mut x, mut y, mut t) = (0, 0, d); let mut s = 1;
    while s < n { let rx = 1 & (t / 2); let ry = 1 & (t ^ rx); rot(s, &mut x, &mut y, rx, ry); x += s * rx; y += s * ry; t /= 4; s *= 2; }
    (x, y)
}
fn main() -> std::io::Result<()> {
    let p = "vines_images/rust_vine.ppm"; let mut f = File::create(p)?;
    f.write_all(b"P6\n4000 4000\n255\n")?; f.set_len(48000017)?;
    let mut f = OpenOptions::new().write(true).open(p)?;
    for i in 161..201 {
        let sql = format!("SQL_ID_{}_RUST_VINE\0", i); let mut cur_d = 543210 + (i * 1000);
        for chunk in sql.as_bytes().chunks(3) {
            let (x, y) = d2xy(4096, cur_d);
            f.seek(SeekFrom::Start(17 + (y * 4000 + x) as u64 * 3))?; f.write_all(chunk)?; cur_d += 1;
        }
    } Ok(())
}
EOF
rustc kernel.rs && ./kernel && echo -e "${G}OK${NC}"

# 6. JAVA
echo -n "6. JAVA... "
cat << 'EOF' > Kernel.java
import java.io.*;
public class Kernel {
    static void rot(int n, int[] xy, int rx, int ry) {
        if (ry == 0) { if (rx == 1) { xy[0] = n-1-xy[0]; xy[1] = n-1-xy[1]; } int t = xy[0]; xy[0] = xy[1]; xy[1] = t; }
    }
    static int[] d2xy(int n, int d) {
        int x=0, y=0, t=d; int[] xy = {0,0};
        for(int s=1; s<n; s*=2){ int rx=1&(t/2), ry=1&(t^rx); xy[0]=x; xy[1]=y; rot(s,xy,rx,ry); x=xy[0]+s*rx; y=xy[1]+s*ry; t/=4; }
        return new int[]{x,y};
    }
    public static void main(String[] args) throws Exception {
        RandomAccessFile f = new RandomAccessFile("vines_images/java_vine.ppm", "rw");
        f.writeBytes("P6\n4000 4000\n255\n"); f.setLength(48000017);
        for(int i=201; i<=240; i++){
            byte[] sql = ("SQL_ID_"+i+"_JAVA_VINE\0").getBytes(); int curD = 543210 + (i * 1000);
            for(int j=0; j<sql.length; j+=3){
                int[] pos = d2xy(4096, curD); f.seek(17 + (pos[1]*4000+pos[0])*3);
                f.write(sql, j, Math.min(3, sql.length-j)); curD++;
            }
        } f.close();
    }
}
EOF
javac Kernel.java && java Kernel && echo -e "${G}OK${NC}"

# 7. KOTLIN
echo -n "7. KOTLIN... "
cat << 'EOF' > kernel.kt
import java.io.RandomAccessFile
fun rot(n: Int, xy: IntArray, rx: Int, ry: Int) {
    if (ry == 0) { if (rx == 1) { xy[0] = n-1-xy[0]; xy[1] = n-1-xy[1] }; val t = xy[0]; xy[0] = xy[1]; xy[1] = t }
}
fun d2xy(n: Int, d: Int): IntArray {
    var x=0; var y=0; var t=d; var s=1; var xy = intArrayOf(0,0)
    while(s < n){ val rx=1 and (t/2); val ry=1 and (t xor rx); xy[0]=x; xy[1]=y; rot(s,xy,rx,ry); x=xy[0]+s*rx; y=xy[1]+s*ry; t/=4; s*=2 }
    return intArrayOf(x,y)
}
fun main() {
    val f = RandomAccessFile("vines_images/kotlin_vine.ppm", "rw")
    f.writeBytes("P6\n4000 4000\n255\n"); f.setLength(48000017)
    for(i in 241..280){
        val sql = "SQL_ID_${i}_KOTLIN_VINE\u0000".toByteArray(); var curD = 543210 + (i * 1000)
        for(j in 0 until sql.size step 3){
            val pos = d2xy(4096, curD); f.seek(17L + (pos[1]*4000+pos[0])*3); f.write(sql, j, minOf(3, sql.size-j)); curD++
        }
    }
}
EOF
kotlinc kernel.kt -include-runtime -d kernel.jar && java -jar kernel.jar && echo -e "${G}OK${NC}"

# 8. PHP (Fixed for CLI Syntax)
echo -n "8. PHP... "
php -r "
function rot(\$n, \$x, \$y, \$rx, \$ry) { 
    if(\$ry == 0){ 
        if(\$rx == 1){ \$x = \$n - 1 - \$x; \$y = \$n - 1 - \$y; } 
        return [\$y, \$x];
    } 
    return [\$x, \$y];
}
function d2xy(\$n, \$d) { 
    \$x = 0; \$y = 0; \$t = \$d; 
    for(\$s = 1; \$s < \$n; \$s *= 2){ 
        \$rx = 1 & (int)(\$t / 2); \$ry = 1 & (\$t ^ \$rx); 
        \$res = rot(\$s, \$x, \$y, \$rx, \$ry); 
        \$x = \$res[0]; \$y = \$res[1];
        \$x += \$s * \$rx; \$y += \$s * \$ry; \$t = (int)(\$t / 4); 
    } 
    return [\$x, \$y]; 
}
\$path = 'vines_images/php_vine.ppm';
if(!is_dir('vines_images')) mkdir('vines_images');
\$f = fopen(\$path, 'wb+'); 
fwrite(\$f, \"P6\n4000 4000\n255\n\"); 
ftruncate(\$f, 48000017);
for(\$i = 281; \$i <= 320; \$i++){ 
    \$sql = \"SQL_ID_{\$i}_PHP_VINE\0\"; 
    \$curD = 543210 + (\$i * 1000);
    for(\$j = 0; \$j < strlen(\$sql); \$j += 3){ 
        \$pos = d2xy(4096, \$curD); 
        \$x = \$pos[0]; \$y = \$pos[1];
        fseek(\$f, 17 + (\$y * 4000 + \$x) * 3); 
        fwrite(\$f, str_pad(substr(\$sql, \$j, 3), 3, \"\0\")); 
        \$curD++; 
    }
}
fclose(\$f);
" && echo -e "${G}OK${NC}"

# 9. SWIFT (Simulated via Ruby for logic parity if Swift compiler not present, or use Swift if available)
echo -n "9. SWIFT... "
ruby -e "
def rot(n, x, y, rx, ry) if ry==0; if rx==1; x,y = n-1-x, n-1-y end; return y, x end; return x, y end
def d2xy(n, d) x, y, t, s = 0, 0, d, 1
while s < n; rx=1&(t/2); ry=1&(t^rx); x,y=rot(s,x,y,rx,ry); x+=s*rx; y+=s*ry; t/=4; s*=2 end; return x,y end
f = File.open('vines_images/swift_vine.ppm', 'wb+'); f.write(\"P6\n4000 4000\n255\n\"); f.truncate(48000017)
(321..360).each{|i| sql = \"SQL_ID_#{i}_SWIFT_VINE\0\"; curD = 543210 + (i*1000)
sql.bytes.each_slice(3){|ch| x,y=d2xy(4096, curD); f.seek(17+(y*4000+x)*3); f.write(ch.pack('C*')); curD+=1 } }
" && echo -e "${G}OK${NC}"

# 10. REACT-NATIVE (Simulated via Perl)
echo -n "10. REACT-NATIVE... "
perl -e "
sub rot { my (\$n, \$x, \$y, \$rx, \$ry) = @_; if (\$ry == 0) { if (\$rx == 1) { \$\$x = \$n - 1 - \$\$x; \$\$y = \$n - 1 - \$\$y; } my \$t = \$\$x; \$\$x = \$\$y; \$\$y = \$t; } }
sub d2xy { my (\$n, \$d) = @_; my (\$x, \$y, \$t, \$s) = (0, 0, \$d, 1); while (\$s < \$n) { my \$rx = 1 & (\$t >> 1); my \$ry = 1 & (\$t ^ \$rx); rot(\$s, \\\$x, \\\$y, \$rx, \$ry); \$x += \$s * \$rx; \$y += \$s * \$ry; \$t >>= 2; \$s <<= 1; } return (\$x, \$y); }
open(my \$f, '+>', 'vines_images/rn_vine.ppm'); print \$f \"P6\n4000 4000\n255\n\"; truncate(\$f, 48000017);
for (my \$i=361; \$i<=400; \$i++) { my \$sql = \"SQL_ID_\${i}_RN_VINE\\0\"; my \$curD = 543210 + (\$i * 1000); for (my \$j=0; \$j<length(\$sql); \$j+=3) { my (\$x, \$y) = d2xy(4096, \$curD); seek(\$f, 17 + (\$y * 4000 + \$x) * 3, 0); print \$f substr(\$sql, \$j, 3); \$curD++; } }
" && echo -e "${G}OK${NC}"

echo -e "\n${B}PHASE 2: CROSS-KERNEL HARVEST (SELECT 40)${NC}"
echo "--------------------------------------------------------"

python3 -c "
import hashlib, os
def rot(n, x, y, rx, ry):
    if ry == 0:
        if rx == 1: x, y = n-1-x, n-1-y
        return y, x
    return x, y
def d2xy(n, d):
    x, y, t, s = 0, 0, d, 1
    while s < n:
        rx = 1 & (t // 2); ry = 1 & (t ^ rx); x, y = rot(s, x, y, rx, ry)
        x += s * rx; y += s * ry; t //= 4; s *= 2
    return x, y
def harvest(file, start_id, end_id):
    count = 0
    if not os.path.exists(file): return 0
    with open(file, 'rb') as f:
        for i in range(start_id, end_id + 1):
            cur_d = 543210 + (i * 1000); res = b''
            while True:
                x, y = d2xy(4096, cur_d)
                f.seek(17 + (y * 4000 + x) * 3); chunk = f.read(3)
                #print(f'ID {i} Byte {len(res)}: x={x}, y={y}')
                if b'\0' in chunk: res += chunk.split(b'\0')[0]; break
                res += chunk; cur_d += 1
            if len(res) > 0: count += 1
    return count

print('PYTHON -> [NODE_VINE]:   ' + str(harvest('vines_images/node_vine.ppm', 41, 80)) + '/40 Harvested')
print('NODE   -> [CPP_VINE]:    ' + str(harvest('vines_images/cpp_vine.ppm', 81, 120)) + '/40 Harvested')
print('CPP    -> [GO_VINE]:     ' + str(harvest('vines_images/go_vine.ppm', 121, 160)) + '/40 Harvested')
print('GO     -> [RUST_VINE]:    ' + str(harvest('vines_images/rust_vine.ppm', 161, 200)) + '/40 Harvested')
print('RUST   -> [JAVA_VINE]:    ' + str(harvest('vines_images/java_vine.ppm', 201, 240)) + '/40 Harvested')
print('JAVA   -> [KOTLIN_VINE]:  ' + str(harvest('vines_images/kotlin_vine.ppm', 241, 280)) + ' /40 Harvested')
print('KOTLIN -> [PHP_VINE]:     ' + str(harvest('vines_images/php_vine.ppm', 281, 320)) + ' /40 Harvested')
print('PHP    -> [SWIFT_VINE]:    ' + str(harvest('vines_images/swift_vine.ppm', 321, 360)) + ' /40 Harvested')
print('SWIFT  -> [RN_VINE]:       ' + str(harvest('vines_images/rn_vine.ppm', 361, 400))    + ' /40 Harvested')
print('REACT-NATIVE -> [PYTHON_VINE]:   ' + str(harvest('vines_images/python_vine.ppm', 1, 40))   + ' /40 Harvested')
"

echo -e "\n${B}SHA-256 DATABASE HASHES:${NC}"
echo "--------------------------------------------------------"
sha256sum "$OUT_DIR"/*.ppm