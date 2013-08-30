// This is the front half of the pt correlation code

#define BUFSIZE 32768

// Includes
#include <iostream>
#include <stdlib.h>
#include <stdio.h>
#include <string>
#include <math.h>
#include <algorithm> //required for std::swap
#include <output.h>
#include <efficiency.h>
#include <sys/stat.h>

using namespace std;

// Prototypes
void trackanalysisfunction(void);
void LoadFiles(void);
void LoadCuts(void);
bool CheckTrack(void);

// Globals
bool Good_Tracks;
int goodMult;
int refMult;
int totalNumberOfevents;
string directory;
const char *Headers[1];
const char *Events[1];

int Total[2000];
int Count[2000];

FILE *fp;
FILE *fh;
int iFile;
int myLocal;
int eventNumber;
int myDisplay;
bool eventCut;
bool etaCut;
bool ptCut;
// Header information
double refMult;
// Event information
short pid;
float pt;
float eta;
float phi;
// Analysis Cuts
double pt_cut[2];
double eta_cut[2];
// Command Line Cuts
double pid_Ccut[3];
double pt_Ccut[3];
double eta_Ccut[3];
double phi_Ccut[3];
double refMult_Ccut[3];

int main(int argc, char* argv[]){
    cout << "Welcome to Display program" << endl;
    directory = "Output/";

    LoadFiles();

    for(int i=0; i<2000; i++){
        Total[i] = 0;
        Count[i] = 0;
    }

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Loading cuts from file" << endl;
    LoadCuts();

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Loading command line cuts" << endl;
    int i = 1;
    while(i != argc){
        if(strcmp(argv[i],"directory")==0){
            directory=argv[i+1];
            i+=2;
            cout << i << endl; cout.flush();
        } else if(strcmp(argv[i],"refMult")==0) { refMult_Ccut[0] = atof(argv[i+1]); refMult_Ccut[1] = atof(argv[i+2]); refMult_Ccut[2] = 1; i+=3;
        } else if(strcmp(argv[i],"pid")==0) { pid_Ccut[0] = atof(argv[i+1]); pid_Ccut[1] = atof(argv[i+2]); pid_Ccut[2] = 1; i+=3;
        } else if(strcmp(argv[i],"pt")==0) { pt_Ccut[0] = atof(argv[i+1]); pt_Ccut[1] = atof(argv[i+2]); pt_Ccut[2] = 1; i+=3;
        } else if(strcmp(argv[i],"eta")==0) { eta_Ccut[0] = atof(argv[i+1]); eta_Ccut[1] = atof(argv[i+2]); eta_Ccut[2] = 1; i+=3;
        } else if(strcmp(argv[i],"phi")==0) { phi_Ccut[0] = atof(argv[i+1]); phi_Ccut[1] = atof(argv[i+2]); phi_Ccut[2] = 1; i+=3;
        }
    }
    string command = "mkdir -p " + directory + "/";
    system(command.c_str());

    totalNumberOfevents = 0;
    myDisplay = 10000;

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Starting Analysis" << endl;


	for(iFile=0;iFile<1;iFile++){
		cout << "Begin file " << iFile+1 << ", " << Events[iFile] << endl;
        	char dBuffer[BUFSIZE];
		fh=fopen(Events[iFile],"rb");
        	//setbuf( fh, dBuffer );
		fread(&goodMult,sizeof(int),1,fh);	
		while(!feof(fh)){
			fread(&refMult,sizeof(double),1,fh);
			myLocal++;
			totalNumberOfevents++;
			if(myLocal == myDisplay){
				cout << "Event " << totalNumberOfevents << " for file " << iFile+1 << " of " << 1 << endl; cout.flush();
				myLocal=0;
			}
			for(int iEvent=0;iEvent<goodMult;iEvent++){
				fread(&pid,sizeof(short),1,fh);
				fread(&pt,sizeof(float),1,fh);
				fread(&eta,sizeof(float),1,fh);
				fread(&phi,sizeof(float),1,fh);
				trackanalysisfunction();
			}
			fread(&goodMult,sizeof(int),1,fh);	
		}
		fclose(fh);
		cout << "Events read from file " << Events[iFile] << " giving " << totalNumberOfevents << endl;
	}
	cout << "Total number of events read = " << totalNumberOfevents << endl;

    cout << "+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=" << endl << "Analysis Finished. Creating Output" << endl;

    fstream Efficiency;
    string fname = directory+"/Efficiency_vs_pt.txt";
    Efficiency.open(fname.c_str(), fstream::out );
    for(int i=0; i<2000; i++){
        if(Total[i] != 0){
            Efficiency << float(i)/1000 << " " << float(Count[i])/float(Total[i]) << endl;
        } else {
            Efficiency << float(i)/1000 << " 0" << endl;
        }
    }

    return 0;
}

void trackanalysisfunction(void){
        //cout << pid << " " ; cout.flush();
	if(CheckTrack()){
                Total[int(pt*1000)] += 1;
                if( eff( pid, pt, eta, phi, 0) > (float(rand()%1000000)/1000000) ){
                          Count[int(pt*1000)] += 1;
                }
        }
}

void LoadFiles(void){
    Events[0] = "/scratch/UrQMD_1000GeV.bin";
}

void LoadCuts(void){
    pt_cut[0] = 0.15;
    eta_cut[0] = -1;
    pt_cut[1] = 2.0;
    eta_cut[1] = 1;
    pid_Ccut[2] = 0;
    pt_Ccut[2] = 0;
    eta_Ccut[2] = 0;
    phi_Ccut[2] = 0;
    refMult_Ccut[2] = 0;
}

bool CheckTrack(void){
    bool good = true;
    if((pt < pt_cut[0]) || (pt > pt_cut[1])) good = false;
    if((eta < eta_cut[0]) || (eta > eta_cut[1])) good = false;
    if((refMult_Ccut[2] == 1) && ((refMult < refMult_Ccut[0]) || (refMult > refMult_Ccut[1]))) good = false;
    if((pid_Ccut[2] == 1) && ((pid < pid_Ccut[0]) || (pid > pid_Ccut[1]))) good = false;
    if((pt_Ccut[2] == 1) && ((pt < pt_Ccut[0]) || (pt > pt_Ccut[1]))) good = false;
    if((eta_Ccut[2] == 1) && ((eta < eta_Ccut[0]) || (eta > eta_Ccut[1]))) good = false;
    if((phi_Ccut[2] == 1) && ((phi < phi_Ccut[0]) || (phi > phi_Ccut[1]))) good = false;
    return good;
}
