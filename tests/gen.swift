import Foundation;import CommonCrypto
let p="parity_images/swift_database.ppm";let d="P6\n4000 4000\n255\n".data(using:.utf8)!+Data(count:48000000)
try? d.write(to:URL(fileURLWithPath:p));let f=FileHandle(forUpdatingAtPath:p)!
for i in 1...4000{let s="Node_Alpha_\(i)ScyWeb_Global_Parity_2026";let data=s.data(using:.utf8)!
var h=[UInt8](repeating:0,count:Int(CC_SHA256_DIGEST_LENGTH))
data.withUnsafeBytes{_ = CC_SHA256($0.baseAddress, CC_LONG(data.count), &h)}
let x=(Int(h[0])<<8|Int(h[1]))%4000;let y=(Int(h[2])<<8|Int(h[3]))%4000
f.seek(toFileOffset:UInt64(17+(y*4000+x)*3));var v="UPDATE user SET status='ACTIVE' WHERE id=\(i)".data(using:.utf8)!
v.append(0);f.write(v)};f.closeFile()
