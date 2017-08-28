/*!
 * \file  CmpExample.c
 * \brief Example to follow to add a component to the system
 *
 * In addition to this file and the corresponding .h, search "ADD_A_COMPONENT"
 * to see what and where you have to do something to add the component properly.
 * Search also "CODING_RULE" to see the coding rules that have to be followed	
 *
 * [ADD_A_COMPONENT] : to add the component X in the system, define a function CmpX in CmpX.c 
 * that will be used by the component manager to initialize the component.
 * In SysMgrAdapt.c, add the #include "CmpX.h" and add the call to your 'CmpX(Hook)' in 'SYSADAPT_CallComponentsHook'
 *
 */
 
#include "rtxcapi.h" /* RTXC Kernel Service prototypes */
#include "rtxcstdio.h"
#include "ktask.h" /* defines TASKA */
#include "ksema.h" /* defines GOSEMA */
#include "kcounter.h" /* defines COUNTER1 */
#include "kproject.h" /* defines CLKTICK */
#include "taskLib.h"
#include "stdint.h"
#include "CmpExample.h"


static int bNewConfReceived = 0;
static int bResetConf = 0;
static int bExampleConfigured = 0;

static void ExampleSysTransitionCallback(E_SYS_STATE FromState, E_SYS_STATE ToState);
static void ExampleTask(void);

//Preetha
static char * const semaname[] = { "SemExampleConfUsed0", "SemSysStateTransition" };
uint8_t example_task_echo_buffer[256];
uint8_t example_task_echo_stack[1024];
SEMA CreateSema(int inum);

#define EXAMPLE_STACK_SIZE	512
#define STACK_ALIGNMENT  8u /* 8 or 16 only; */


/*! 
 * \var static SEM_ID SemExampleConfUsed    
 * \brief Semaphore to ensure configuration of this component will be used only when allowed
 * 
 * [ADD_A_COMPONENT] : just an example but you can use this method
 *
 */
//Preetha
//static SEM_ID SemExampleConfUsed;
static SEMA SemExampleConfUsedQ;

/*! 
 * \fn E_RES_HOOK_CALL CmpExample(E_CMP_HOOKS hook)
 * \brief Function that defines the life cycle of CmpExample component
 *
 * [ADD_A_COMPONENT] : must be called in 'SYSADAPT_CallComponentsHook' of SysMgrAdapt.c
 *
 * \param hook: step of the life cycle
 * \return E_RES_HOOK_CALL: HOOK_CALL_FATALERROR only for fatal errors, HOOK_CALL_OK otherwise
 */
E_RES_HOOK_CALL CmpExample(E_CMP_HOOKS hook)
{
	int bConfigurationAllowed;
	TASK_ID ExTaskId;

    switch(hook)
    {
    case CMP_INITHW:
		// [ADD_A_COMPONENT] : Initialize hardware related to the component in this Hook
		break;
		
    case CMP_INITVAR:
                // [ADD_A_COMPONENT] : Initialize variables related to the component in this Hook
                // [ADD_A_COMPONENT] example: Create semaphore that will be used to be sure to process only when configured
              
                //Preetha
                //SemExampleConfUsed = semMCreate(SEM_Q_PRIORITY | SEM_INVERSION_SAFE);
                SemExampleConfUsedQ = CreateSema(0);
		
		// Register callback functions for Example component
		// [ADD_A_COMPONENT] : if the component has actions to be performed within a System State transition,
		// register the corresponding callbacks here :
		SYS_RegisterStateTransitionCallback(ExampleSysTransitionCallback, SYS_CONFIGURED, (int)CONFIGURED_EXAMPLE_RANK_CALLBACK);
		SYS_RegisterStateTransitionCallback(ExampleSysTransitionCallback, SYS_NO_CONF, (int)NOCONF_EXAMPLE_RANK_CALLBACK);
		SYS_RegisterStateTransitionCallback(ExampleSysTransitionCallback, SYS_FATAL_ERROR, (int)FATALERROR_EXAMPLE_RANK_CALLBACK);
		break;
		
    case CMP_INITTASKS:
	// [ADD_A_COMPONENT] : if needed, create tasks of the component here (priority will be overwritten if task is defined in SYSADAPT_SystemTasks)
        /* taskSpawn(char *name,int priority,int option,int stacksize,FUNCPTR entrypoint,int avg1,avg2....avg10)
            1. name: task name examp: task1
            2. priority: 0-255 //0---high, 255---low
            3.options: 0 most of the times
            4.FUNCPTR: It jumps to function we are calling examp; (FUNCPTR)fun1
            5.avg1--avg10: almost 0 every time*/
        
          //Preetha
          /*  ExTaskId = taskSpawn("ExampleTask", DEFAULT_TASK_CREATION_PRIORITY, VX_FP_TASK, EXAMPLE_STACK_SIZE, (FUNCPTR) ExampleTask,0, 0, 0, 0, 0, 0, 0, 0, 0, 0);*/
          
          /* Create and start task */
          TASK task;
          TASKPROP  taskprop;
          KSRC         ksrc;                  
         
          ksrc = KS_OpenTask( "ExampleTask", &task );
          if ( ksrc == RC_GOOD )
          {
              taskprop.taskentry = ExampleTask; //Probably this is the funcptr equivalent of vxworks ?? Preetha plz check
              taskprop.stackbase = (char *)( ( ( (uintptr_t)example_task_echo_stack ) + STACK_ALIGNMENT - 1 ) & ~( STACK_ALIGNMENT - 1 ) );
              taskprop.stacksize = ( sizeof( example_task_echo_stack ) - ( (uintptr_t)taskprop.stackbase - (uintptr_t)example_task_echo_stack  ) ) & ~( STACK_ALIGNMENT - 1 );
              taskprop.priority  = HookToTask(task);

              KS_DefTaskProp( task, &taskprop );
              KS_DefTaskPriority( task, taskprop.priority );
              KS_ExecuteTask( task );
          }
          else
          { 
              // Fatal error
              return HOOK_CALL_FATALERROR;
          }
    	break;
		
    case CMP_LASTINIT:
		// Perform last initializations before component manager goes into CMP_CYCLE (each 50 ms) until next reboot
		break;
		
    case CMP_CYCLE:
        // Called by the CmpMgr (low priority) each 50 ms once previous hooks have been exectuded once		
        // [ADD_A_COMPONENT] : put in this hook low priority actions that are not managed by the ExampleTask        
        // For example we simulate System State transitions that may be involved by a new configuration received :
      
        //Preetha - TestCode      
        KSRC ksrc_cmp_cycle;
       
        if (bNewConfReceived)
     //   if(1) - Preetha - use this for testing / debugging
        {
			bNewConfReceived = 0;			
			bConfigurationAllowed = 0;
			            
                        // [ADD_A_COMPONENT] begin : example of how to make a System State transition 
			// First lock the transition for other components

			//Preetha - TestCode
                        ksrc_cmp_cycle = SYS_LockStateTransition("SemSysStateTransition");  
                                       
                        if(ksrc_cmp_cycle != RC_GOOD)
                        {               
                           // Fatal error
                           SYS_FatalError("SysManager: Use Semaphore failed\n");
                        }
                                                
			// Here for example we can call a function from another component to see if the transition can be done
			// We also check the System State is in the expected state (and if so it won't be changed until SYS_StateTransition or SYS_UnlockStateTransition is called)
			if  ((SYS_GetState() == SYS_CONFIGURED) /* && EX2_IsOkForNoconfTransition()*/)
			{
				// The system is able to accept a new configuration =>
				// Transition to NO_CONF can be performed (components that registered a function on this event will be able to unconfigure)
				SYS_StateTransition(SYS_NO_CONF);
			}
			else
			{
				// We don't have to perform the transition => unlock state transition
                                //Preetha - TestCode
				SYS_UnlockStateTransition();  
			}

			//Preetha
                        //SYS_LockStateTransition();                        
                        ksrc_cmp_cycle = SYS_LockStateTransition("SemSysStateTransition");                         
               
                        if(ksrc_cmp_cycle != RC_GOOD)
                        {               
                           // Fatal error
                           SYS_FatalError("SysManager: Use Semaphore failed\n");
                        }
                        
			if  (SYS_GetState() == SYS_NO_CONF)
			{
				// Now perform a transition to CONFIGURING to warn other components a configuration is in progress
				SYS_StateTransition(SYS_CONFIGURING);
				
				// Configuration by this component is allowed 
				// => remember this to be able to perform configuration outside the lock transition 
				bConfigurationAllowed = 1;
			}
			else
			{
				// We don't have to perform the transition => unlock state transition
				SYS_UnlockStateTransition();                                
			}
			// [ADD_A_COMPONENT] end

                        // [ADD_A_COMPONENT]: important note:
                        // System transitions can not be initiated inside ISR
			
			if (bConfigurationAllowed)
			{
				// Perform the configuration transfer
								
				// Configuration has been written => System transition to CONFIGURED can be performed
				// First lock the transition for other components
                                
                                //Preetha
				//SYS_LockStateTransition();                          
                                //ksrc_cmp_cycle = KS_UseSema ("SemSysStateTransition", &sema_cmp_cycle);                          
                                ksrc_cmp_cycle = SYS_LockStateTransition("SemSysStateTransition"); 
               
                                if(ksrc_cmp_cycle != RC_GOOD)
                                {               
                                   // Fatal error
                                   SYS_FatalError("SysManager: Use Semaphore failed\n");
                                }
				// Then we check the System State is in the expected state
				if (SYS_GetState() == SYS_CONFIGURING)
				{
					// [ADD_A_COMPONENT] 
					// For example we can use a function to check that the configuration is valid
					// and then choose to perform a transition to SYS_CONFIGURED (or SYS_NO_CONF if configuration is not valid)
					//if  (CFG_IsConfValid())
					//{
						// Transition to CONFIGURED can be performed
						SYS_StateTransition(SYS_CONFIGURED);
					//}
					//else
					//{
						// Transition to NO_CONF must be performed as configuration is not valid
						//SYS_StateTransition(SYS_NO_CONF);
					//}
				}
				else
				{
					// Another component changed the System State during configuration
					// In our example it would necessarily be FATAL_ERROR => do not do anything except unlock transition
					SYS_UnlockStateTransition();                                  
				}
			}
			else
			{
				// Return an error
			}
        }
        

        if (bResetConf)
        {
            bResetConf = 0;
            
            //Preetha
            //SYS_LockStateTransition();
            // ksrc_cmp_cycle = KS_UseSema ("SemSysStateTransition", &sema_cmp_cycle);
            ksrc_cmp_cycle = SYS_LockStateTransition("SemSysStateTransition"); 
               
            if(ksrc_cmp_cycle != RC_GOOD)
            {               
                // Fatal error
                SYS_FatalError("SysManager: Use Semaphore failed\n");
            }
                        
            SYS_StateTransition(SYS_NO_CONF);  
        }
        
		break;
		
	default:
		break;
	}
	
	return HOOK_CALL_OK;
}

//Preetha - In Future, Plz make a common file for all Quadros related Application API's 
//Plz dont mix the application code with Quadros related API IMPLEMENTATION details
SEMA CreateSema(int inum)
{
    KSRC retcode;
    SEMAPROP semaprop = { 0 };
    SEMA sema;

    retcode = KS_OpenSema(semaname[inum], &(sema) );

    if (retcode != RC_GOOD)
    {
        /* error opening semaphore */
        return 0;
    }

    KS_DefSemaProp(sema, &(semaprop) );

    return sema;
}

/*! 
 * \fn static void ExampleTask(void)
 * \brief Function for "ExampleTask" task
 *
 * [ADD_A_COMPONENT] : the component can create its own tasks. Just an example, not mandatory
 */
static void ExampleTask(void)
{
        KSRC ksrc;
        SEMA sema;
  
        while(1)
	{
	       // Take the semaphore that ensure we won't change the configuration in between
		
               //semTake(SemExampleConfUsed, WAIT_FOREVER);
               //Preetha - TestCode                
               ksrc = KS_UseSema ("SemExampleConfUsed0", &SemExampleConfUsedQ);
               
               if(ksrc != RC_GOOD)
               {               
                  // Fatal error
                  SYS_FatalError("SysManager: Use Semaphore failed\n");
               } 
                //Preetha - TestCode ends here
          
		if (SYS_GetState() == SYS_CONFIGURED)
		{
			// [ADD_A_COMPONENT] : In this example we have to perform something only when configured
			// Here we are sure that between the semTake and the semGive no transition to NO_CONF nor CONFIGURED can be done 
			// See below SemExampleConfUsed in ExampleSysTransitionCallback
			
			// Note: in monocore system this task has no chance to be scheduled during a system state transition
			// as the task performing the transistion has higher priority
			// but in multicore system, if the task that performs the transition is executing on another core, this task may run
			// and in this case SYS_GetState() will return SYS_TRANSITION_IN_PROGRESS 
			
			if (!bExampleConfigured)
			{
				// Should be impossible
				//logMsg("SYSMANAGER FATAL ERROR !!! \n",0,0,0,0,0,0);
                                SYS_FatalError("SYSMANAGER FATAL ERROR !!\n");
				
                                //semGive(SemExampleConfUsed);
                                //Preetha - TestCode                                
                                KS_CloseSema (SemExampleConfUsedQ);                          
                                
			}		
		}
				
	       //Preetha - TestCode               
               //semGive(SemExampleConfUsed);
               KS_CloseSema (SemExampleConfUsedQ); 		
		
               //taskDelay(1);
               KS_SleepTask (COUNTER1, (TICKS)1/CLKTICK);
	}
}


/*! 
 * \fn static void ExampleSysTransitionCallback(E_SYS_STATE FromState, E_SYS_STATE ToState)
 * \brief Function that will be called within the System State transitions (see SYS_RegisterStateTransitionCallback)
 * 
 * [ADD_A_COMPONENT] : it is NOT allowed to perform any system transition in this function !
 * 
 * \param FromState: the system state before the transition
 * \param ToState: the system state we are transit to
 */
static void ExampleSysTransitionCallback(E_SYS_STATE FromState, E_SYS_STATE ToState)
{	
	KSRC ksrc;
        SEMA sema;
  
        // If needed we can know what is the current state we are about to leave
	switch (FromState)
	{
	case SYS_NO_CONF: 
		break;
	case SYS_CONFIGURED: 
		break;
	case SYS_FATAL_ERROR: 
		break;
	default:
		break;
	}
	
	// then perform actions depending on the state we are about to enter
	switch (ToState)
	{
	case SYS_NO_CONF: 
              // Preetha - TestCode        
              //semTake(SemExampleConfUsed, WAIT_FOREVER);              
               ksrc = KS_UseSema ("SemExampleConfUsed0", &SemExampleConfUsedQ);
                   
               if(ksrc != RC_GOOD)
               {               
                   // Fatal error
                   SYS_FatalError("SysManager: Use Semaphore failed\n");
               } 
		
		// [ADD_A_COMPONENT] : one (and only one) component may call the CFG_DeleteConf function on SYS_NOCONF_EVT
		// (antoher possibility is to call it directly when a component wants to go to NO_CONF)
		//CFG_DeleteConf();
		
		// Simulate our component is not configured
		bExampleConfigured = 0;
		
		//Preetha
                //semGive(SemExampleConfUsed);
                KS_CloseSema (SemExampleConfUsedQ);   
		
		// Do potential other deconfiguration work ...
		break;
                
	case SYS_CONFIGURED: 	
		// Preetha
                //semTake(SemExampleConfUsed, WAIT_FOREVER);
                ksrc = KS_UseSema ("SemExampleConfUsed0", &SemExampleConfUsedQ);
                   
                if(ksrc != RC_GOOD)
                {               
                   // Fatal error
                   SYS_FatalError("SysManager: Use Semaphore failed\n");
                } 
		
		// Simulate our component is configured
		bExampleConfigured = 1;
		
		// Preetha
                //semGive(SemExampleConfUsed);
                KS_CloseSema (SemExampleConfUsedQ);  
		break;
                
	case SYS_FATAL_ERROR: 
		break;
                
	default:
		break;
	}
}


/*! 
 * \fn void EXAMPLE_FunctionToBeExportedToOutside(void)   
 * \brief Just an example to point out the following coding rules:
 * 
 * [CODING_RULE] : function of CmpExample component exported to another component must be declared in CmpExample.h
 *
 * [CODING_RULE] : naming convention is <ComponentName>_NameOfTheFunction. <ComponentName> might be shorten
 */
void EXAMPLE_FunctionToBeExportedToOutside(void)
{
	return;
}


