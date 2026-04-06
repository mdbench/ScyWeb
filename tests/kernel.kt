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
