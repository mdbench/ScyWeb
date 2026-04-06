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
