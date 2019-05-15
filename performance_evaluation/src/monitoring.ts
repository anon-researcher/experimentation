import * as os from 'os';
import * as fs from "fs";
import {WriteStream} from "fs";

export class Monitoring {

    stop = false;
    timeout:number;
    outstream:WriteStream;

    constructor(timeout: number, outpath:string) {
        this.stop = false;
        this.timeout = timeout;
        this.outstream = fs.createWriteStream(outpath, {flags:'a'});
    }

    // function to get CPU information
    private static cpuAverage(): {} {

        //Initialise sum of idle and time of cores and fetch CPU info
        let totalIdle: number = 0, totalTick: number = 0;
        let cpus = os.cpus();

        let cpu_stats = [];
        //Loop through CPU cores
        for(let i = 0, len = cpus.length; i < len; i++) {

            //Select CPU core
            let cpu: any = cpus[i];

            let cpu_core = {
                totalTick: 0,
                totalIdle: 0
            };

            //Total up the time in the cores tick
            for(let type in cpu.times) {
                totalTick += cpu.times[type];
                cpu_core.totalTick += cpu.times[type];
            }

            //Total up the idle time of the core
            totalIdle += cpu.times.idle;
            cpu_core.totalIdle += cpu.times.idle;

            cpu_stats.push(cpu_core);
        }

        return {
            idle: totalIdle / cpus.length,
            total: totalTick / cpus.length,
            cpuStats: cpu_stats,
            hrTime: process.hrtime.bigint()};
    }

    startMeasurement():void {
        //get first CPU measure
        let prevMeasure = Monitoring.cpuAverage();

        // trigger continuous measurements
        setTimeout(() => this.measure(prevMeasure), this.timeout);
    }

    stopMeasurement() {
        this.stop = true;
    }

    private measure(prevMeasure: any):void {
        // get current measure
        let currentMeasure:any = Monitoring.cpuAverage();

        // calculate the difference in idle and total time between the measures
        let idleDifference = currentMeasure.idle - prevMeasure.idle;
        let totalDifference = currentMeasure.total - prevMeasure.total;

        // calculate the average percentage CPU usage
        let corePercentages : number[] = [];
        let percentageCPU = Math.round(100*(100.0 - (100 * idleDifference / totalDifference)))/100;

        currentMeasure.cpuStats.forEach((entry : any, index : any) => {
            let coreIdleDiff = entry.totalIdle - prevMeasure.cpuStats[index].totalIdle;
            let coreTotalDiff = entry.totalTick - prevMeasure.cpuStats[index].totalTick;

            corePercentages.push(Math.round(100*(100.0 - (100 * coreIdleDiff / coreTotalDiff)))/100);
        });

        // console.log("cpu: " + percentageCPU + " %, freeMem: " + os.freemem() / (1024*1024) + " MB, totalMem: " + os.totalmem()  / (1024*1024));
        this.outstream.write(Date.now() + "," + percentageCPU + "," + os.freemem() / (1024*1024) + "," + os.totalmem() / (1024*1024) + "," + corePercentages.join(",") + "\n");

        if(!this.stop) {
            setTimeout(() => this.measure(currentMeasure), this.timeout);
        }else{
            this.outstream.end();
        }
    }
}

if(process.argv.length !== 4) {
    console.log("Usage: node monitoring.js <outfile> <timeout>");
    process.exit();
}

let timeout = parseInt(process.argv[3]);
let cpu = new Monitoring(timeout, process.argv[2]);

cpu.startMeasurement();
