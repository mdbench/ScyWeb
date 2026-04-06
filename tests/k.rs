use std::fs::{File,OpenOptions}; use std::io::{Write,Seek,SeekFrom};
fn rot(n:i32,x:&mut i32,y:&mut i32,rx:i32,ry:i32){ if ry==0 { if rx==1 { *x=n-1-*x; *y=n-1-*y; } let t=*x; *x=*y; *y=t; } }
fn d2xy(n:i32,d:i32)->(i32,i32){ let (mut x,mut y,mut t)=(0,0,d); let mut s=1; while s<n { let rx=1&(t/2); let ry=1&(t^rx); rot(s,&mut x,&mut y,rx,ry); x+=s*rx; y+=s*ry; t/=4; s*=2; } (x,y) }
fn main()->std::io::Result<()>{
    let p="vines_images/rust_vine.ppm"; let mut f=File::create(p)?; f.write_all(b"P6\n4000 4000\n255\n")?; f.set_len(48000017)?;
    let mut f=OpenOptions::new().write(true).open(p)?; let h=543210;
    for i in 161..201 {
        let mut s=format!("SQL_ID_{}_DATA",i).into_bytes(); s.push(0); let mut cur=h+(i*1000);
        for chunk in s.chunks(3) {
            let (x,y)=d2xy(4096,cur); let mut c=[0u8;3]; c[..chunk.len()].copy_from_slice(chunk);
            f.seek(SeekFrom::Start(17+(y*4000+x) as u64*3))?; f.write_all(&c)?; cur+=1;
        }
    } Ok(())
}
