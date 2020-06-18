vs=1;
os=0; 
cs=1;
rs=0;
rsps=0;
rsms=0;
is=1;
fin_demW='..\dem\DEM_southtyrol.asc';
fin_folder='..\17112011_configHintereis\';
fin_imfolder='slr_ufs\'; 
if is==1                                                                   %KEEP
    fin_imformat='.png';
end
if vs==0 && is==1                                                           %KEEP
    fin_vsformat='.view.asc';
elseif vs==0 && is==0                                                       %KEEP
        fin_viewW='XYZ.view.asc';
end                                                                        %KEEP
if os>0 && is==1                                                            %KEEP
    fin_gcpformat='.gcp.txt';    
end                                                                        %KEEP
cam(:,1)=[6.142488e+05, 5.163441e+06]; % altitude will be calculated!
if vs==1                                                                   %KEEP
    buffer_radius=100; % in  [m]    
end                                                                        %KEEP
cam(:,2)=[6.184486e+05, 5.157440e+06]; % altitude will be calculated!
cam_off=[6, 40]; 
cam_rol=0; 
cam_foc=0.018;
cam_hei=0.0148; 
cam_wid=0.0222; 
if cs>0                                                                %KEEP
    thres_b_orig=127;                                                      %keep
    movavgwindow=5;
end                                                                %KEEP
if os>1                                                                    %KEEP
    UBD=[50, 50, 50, 3, 100, 100, 100, 0.00010, 0, 0];
    LBD=[-50, -50, -50, -3, -100, -100, -100, -0.00010, 0, 0];
    DDS_R_os=0.2;                                                          %keep
    DDS_MaxEval_os=3000;                                                   %keep
    if os==3                                                               %KEEP
        gcpRMSE_optthres=1;
        gcpRMSE_countthres=10;
    end                                                                    %KEEP
end                                                                       %KEEP
if os>0
    os_MarkSiz=8;
end
cs_MarkSiz=6;
