package main
import ("os";"fmt")
func rot(n,x,y,rx,ry int) (int,int) { if ry==0 { if rx==1 { x,y=n-1-x,n-1-y }; return y,x }; return x,y }
func d2xy(n,d int) (int,int) { x,y,t:=0,0,d; for s:=1;s<n;s*=2 { rx:=1&(t/2); ry:=1&(t^rx); x,y=rot(s,x,y,rx,ry); x+=s*rx; y+=s*ry; t/=4 }; return x,y }
func main() {
    p:="vines_images/go_vine.ppm"; f,_:=os.Create(p); f.Write([]byte("P6\n4000 4000\n255\n")); f.Truncate(48000017); f.Close()
    f,_=os.OpenFile(p,os.O_RDWR,0644); h:=543210
    for i:=121;i<=160;i++ {
        s:=fmt.Sprintf("SQL_ID_%d_DATA\x00",i); cur:=h+(i*1000)
        for j:=0;j<len(s);j+=3 {
            x,y:=d2xy(4096,cur); end:=j+3; if end>len(s){end=len(s)}; c:=make([]byte,3); copy(c, s[j:end])
            f.WriteAt(c,int64(17+(y*4000+x)*3)); cur++
        }
    }
}
