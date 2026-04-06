import java.io.*;
public class K {
    static void rot(int n,int[] xy,int rx,int ry){ if(ry==0){ if(rx==1){ xy[0]=n-1-xy[0]; xy[1]=n-1-xy[1]; } int t=xy[0]; xy[0]=xy[1]; xy[1]=t; } }
    static int[] d2xy(int n,int d){ int x=0,y=0,t=d; int[] xy={0,0}; for(int s=1;s<n;s*=2){ int rx=1&(t/2),ry=1&(t^rx); xy[0]=x; xy[1]=y; rot(s,xy,rx,ry); x=xy[0]+s*rx; y=xy[1]+s*ry; t/=4; } return new int[]{x,y}; }
    public static void main(String[] args) throws Exception {
        RandomAccessFile f=new RandomAccessFile("vines_images/java_vine.ppm","rw"); f.writeBytes("P6\n4000 4000\n255\n"); f.setLength(48000017);
        for(int i=201;i<=240;i++){
            byte[] s=("SQL_ID_"+i+"_DATA\0").getBytes(); int cur=543210+(i*1000);
            for(int j=0;j<s.length;j+=3){
                int[] p=d2xy(4096,cur); f.seek(17+(p[1]*4000+p[0])*3); byte[] c=new byte[]{0,0,0};
                System.arraycopy(s,j,c,0,Math.min(3,s.length-j)); f.write(c); cur++;
            }
        } f.close();
    }
}
