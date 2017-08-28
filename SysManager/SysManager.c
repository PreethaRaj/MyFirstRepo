/*!
 * \file SysManager.c
 * \brief The System Manager manages the components live cycle of the system and the System States transitions
 *
 * The System manager is responsible to manage the life cycle of the components (mainly initialization phases) 
 * and provides interfaces to those latters 
 * - to register callback functions that will be called within system state transitions 
 * - to perform safely system states transition
 *
 * The System Manager must be adapted to the platform (see "SYSMGR_ADAPTATION"and SysMgrAdapt sub-folder)
 *  
 * To include a component, take as an example the CmpExample folder and search "ADD_A_COMPONENT"
 * to see where you have to do something
 */

 
#include "rtxcapi.h" /* RTXC Kernel Service prototypes */
//#include "taskLib.h"
#include "ktask.h" /* defines TASKA */
#include "ksema.h" /* defines GOSEMA */
#include "kcounter.h" /* defines COUNTER1 */
#include "kproject.h" /* defines CLKTICK */
//#include "semLib.h"
#include <string.h>
#include "SysManager.h"
#include "stdint.h"
#include "SysMgrAdapt/SysMgrAdaptPriv.h"


/*! 
 * \var static E_SYS_STATE SysState    
 * \brief State of the System   
 *
 * Components may perform a System State transition by calling SYS_StateTransition
 * Components may read the System State by calling SYS_GetState
 * The System States definition is part of the
 */
static E_SYS_STATE SysState;


/*! 
 * \var static TASK_ID CmpMgrTaskId    
 * \brief Task identifier of CmpMgrTask 
 *
 */
//static TASK_ID CmpMgrTaskId;


/*! 
 * \var static SEM_ID SemSysStateTransition    
 * \brief Semaphore to ensure consistent state transition 
 *
 * For more information see SYS_LockStateTransition, SYS_StateTransition and SYS_UnlockStateTransition
 */
//Preetha
//static SEM_ID SemSysStateTransition;
static SEMA SemSysStateTransitionQ;


/*! 
 * \var static SYS_STATE_TRANSITION_FCT *pSysStatesFunc[SYS_NB_STATES]    
 * \brief Array that will contain the pointers to the callback functions associated to each E_SYS_STATE
 *
 * Filled by SYS_RegisterStateTransitionCallback 
 */
static SYS_STATE_TRANSITION_FCT *pSysStatesFunc[SYS_NB_STATES];

/*! 
 * \var static UINT SysStatesNbCallbacks[SYS_NB_STATES]    
 * \brief Number of callbacks associated to each E_SYS_STATE
 *
 * This information is provided by SYSADAPT_GetNbCallbacks() that must be provided by the adaptation layer
 */
static unsigned int SysStatesNbCallbacks[SYS_NB_STATES];


static void CmpMgrTask(void);
static void SysHookTasksCreation(TASK tid);

//Preetha
uint8_t CmpMgr_task_echo_buffer[256];
uint8_t CmpMgr_task_echo_stack[1024];

#define STACK_ALIGNMENT  8u /* 8 or 16 only; */

 
/*! 
 * \fn void SYS_Init(void)    
 * \brief Initialize and launch System Manager   
 *
 */
void SYS_Init(void)
{    
    int i;
    unsigned int NbCallbacks;
    
    // Set SysState to initial state provided by adaptation layer
    SysState = SYSADAPT_InitialState;

    // Create semaphore that will be used to lock the system state transition
    //Preetha - TestCode
    //SemSysStateTransition = semMCreate(SEM_Q_PRIORITY | SEM_INVERSION_SAFE);    
     SemSysStateTransitionQ = CreateSema(1);

	//taskCreateHookAdd - This function adds a 'routine', that will be called everytime a new task is created
	//The routine here is the SysHookTasksCreation
	//SysHookTasksCreation - This fn adjusts the core affinity and prio of the task, if the task is part of SYSAdapt_SystemTasks.
	/*if (taskCreateHookAdd((FUNCPTR)&SysHookTasksCreation) != OK)
	{
		// Fatal error
		SYS_FatalError("SysManager: taskCreateHookAdd failed\n");
	}*/
        
        //Preetha - plz check if this code snippet will work correctly.
        //TestCode : Call the SysHookTaskCreation everytime a task is created successfully
        TASK current_taskid;
        char *pname;        
        KSRC  ksrcO;
        
        //Retrieve the current taskId
        current_taskid = KS_GetTaskID ();
        //Retrieve current task name from taskid
        pname = KS_GetTaskName (current_taskid);
                       
        ksrcO = KS_OpenTask( pname, &current_taskid );
        if ( ksrcO == RC_GOOD )
        {        
          //Initiate system hook task creation manually  
          SysHookTasksCreation(current_taskid);          
        }
        //Testcode ends here : Preetha.  
	
    
    for (i=0; i<SYS_NB_STATES; i++)
    {
    	NbCallbacks = SYSADAPT_GetNbCallbacks(i);//based on the defined enums for each state
    	// Save number of callbacks associated to the system state <i>
    	SysStatesNbCallbacks[i] = NbCallbacks;
    	pSysStatesFunc[i] = NULL;//Array containing pointers to callback functions
    	if (NbCallbacks > 0)
    	{
           
          //Preetha : Error[Pe513]: a value of type "int" cannot be assigned to an entity of type "SYS_STATE_TRANSITION_FCT *"       
           //pSysStatesFunc[i] = malloc(NbCallbacks*sizeof(SYS_STATE_TRANSITION_FCT));
                
           pSysStatesFunc[i] = (SYS_STATE_TRANSITION_FCT*)malloc(NbCallbacks*sizeof(SYS_STATE_TRANSITION_FCT));
    	   //if (pSysStatesFunc[i] == NULL)
           if(pSysStatesFunc[i] == NULL)
    	   {
    		// Fatal error
    		SYS_FatalError("SysManager: malloc failed\n");
    	   }
    	}
    }
        
	
        //Preetha - create a Quadros task 
        /*CmpMgrTaskId = taskSpawn("CmpMgrTask", DEFAULT_TASK_CREATION_PRIORITY, VX_FP_TASK, CMP_MGR_STACK_SIZE, (FUNCPTR) CmpMgrTask,
                                                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0);*/
        
         /* Create and start task */
          TASK task;
          TASKPROP  taskprop;
          KSRC      ksrc; 
          int priority;
          
         
          ksrc = KS_OpenTask( "CmpMgrTask", &task );
          if ( ksrc == RC_GOOD )
          {
              taskprop.taskentry = CmpMgrTask;
              taskprop.stackbase = (char *)( ( ( (uintptr_t)CmpMgr_task_echo_stack ) + STACK_ALIGNMENT - 1 ) & ~( STACK_ALIGNMENT - 1 ) );
              taskprop.stacksize = ( sizeof( CmpMgr_task_echo_stack ) - ( (uintptr_t)taskprop.stackbase - (uintptr_t)CmpMgr_task_echo_stack  ) ) & ~( STACK_ALIGNMENT - 1 );
              taskprop.priority  = HookToTask(task);
              
              KS_DefTaskProp( task, &taskprop );
              KS_DefTaskPriority( task, taskprop.priority );            
                     
              KS_ExecuteTask( task );
          }
          else
          { 
              // Fatal error
              // return HOOK_CALL_FATALERROR;
              // Fatal error
              SYS_FatalError("SysManager: taskSpawn failed\n");
          }       
   
	/*if (CmpMgrTaskId == TASK_ID_ERROR)
	{
		// Fatal error
		SYS_FatalError("SysManager: taskSpawn failed\n");
	}*/
}

//Preetha
int HookToTask(tid)
{
        int i;
	char *NameOfTask;
	int bFinished = FALSE;
        int prio = 0;
	
        NameOfTask = KS_GetTaskName (tid);
	
	// Find if it belongs to our system tasks
	i = 0;
	do
	{
		if (strcmp(SYSADAPT_SystemTasks[i].name, "") == 0) 
		{
			// All the task array has been scanned => go out of the loop
			bFinished = TRUE;
		}
		else if (strcmp(SYSADAPT_SystemTasks[i].name, NameOfTask) == 0) 
		{	                                
                        prio = SYSADAPT_SystemTasks[i].priority;
                        // We found the task => go out of the loop
			bFinished = TRUE;
		}
		i++;		
	} while (!bFinished);
        
        return prio;
}


/*! 
 * \fn static void CmpMgrTask(void)  
 * \brief Task that manages the live cycle of all the components of the system
 *
 * It is used to start up all components allowing them to perform their initialisations
 * (that may be ordered between each component by playing with the number of hooks if needed)
 * until they reach the "CMP_CYCLE" one that will be then called periodically each CMP_CYCLE_PERIOD_IN_MS ms
 */
static void CmpMgrTask(void)
{
	E_CMP_HOOKS i;
    
	// Initialize all components
	for (i=CMP_INITHW_FIRST; i<CMP_CYCLE; i++)
	{
		SYSADAPT_CallComponentsHook(i);
	}
		
        while(1)
        {
            SYSADAPT_CallComponentsHook(CMP_CYCLE);
            //Preetha : TestCode
            //taskDelay(CMP_CYCLE_PERIOD_IN_MS);
            KS_SleepTask (COUNTER1, (TICKS)CMP_CYCLE_PERIOD_IN_MS/CLKTICK);
        }
}



/*! 
 * \fn void SYS_LockStateTransition(void) 
 * \brief Lock the state transition ability (must not be called in ISR context)
 *
 * Must be called by a component before it calls SYS_StateTransition.
 * When a component wants to initiate a System State transition (see SYS_StateTransition), it must first
 * call this function which will ensure no other component (with a higher task priority for example)
 * will make a transition during this one (if it respects the process obviously).
 * This way it may look at current system state with no possibility that another component modify it
 * and thus do the appropriate transition accordingly.
 * 
 * After a call to SYS_LockStateTransition, a call 
 * - to SYS_StateTransition OR
 * - to SYS_UnlockStateTransition 
 * must be done.
 * 
 */
//Preetha - Modified this function to have the ret value as KSRC status and input as semaphore name 
KSRC SYS_LockStateTransition(const char *pname)
{  
   // semTake(SemSysStateTransition, WAIT_FOREVER);
    KSRC ksrc_cmp_cycle;
    
    ksrc_cmp_cycle = KS_UseSema (pname, &SemSysStateTransitionQ);
    return ksrc_cmp_cycle;
}


/*! 
 * \fn void SYS_UnlockStateTransition(void)
 * \brief Unlock the state transition ability (must not be called in ISR context)
 *
 * Must be called by a component after it has called SYS_LockStateTransition without performing 
 * System State transition (no call to SYS_StateTransition)
 */
//Preetha - TestCode   
void SYS_UnlockStateTransition(void)
{       
    //semGive(SemSysStateTransition);
  KS_CloseSema (SemSysStateTransitionQ); 
}
  



/*! 
 * \fn void SYS_StateTransition(E_SYS_STATE State)
 * \brief Perform System State transition (must not be called in ISR context).
 *
 * The following rules have to be followed:
 * 1) A call to SYS_LockStateTransition must be done first (this way current system state may be evaluate safely)
 * 2) A call to SYS_StateTransition (if transition has to be performed) or to SYS_UnlockStateTransition 
 *   (if transition can not be performed) must be done after
 *
 * \param State: the system state transition the caller wants to perform
 */
void SYS_StateTransition(E_SYS_STATE State)
{
	int i;
	//int Prio;
        E_SYS_STATE OldState;   
        
	// At this stage, the SemSysStateTransition MUST have been taken previously by the caller 
	// by a call to SYS_LockStateTransition
    
	// Save the normal priority of the calling task (because the current priority
	// may be affected by priority inversion algorithm)
	//taskPriNormalGet(0, &Prio);
                     
	//Preetha - TestCode
        PRIORITY Prio;
        Prio = KS_GetTaskPriority (0);
	
	// Set now the priority of the calling task to 
	// SYS_MGR_TASK_PRIO (MUST be higher pririty of tasks performing System States transitions)
	
        //taskPrioritySet(0, SYS_MGR_TASK_PRIO);
	//Preetha : Testcode
         KS_DefTaskPriority(0, SYS_MGR_TASK_PRIO);    
        
        
	// Save the current state before we set it to SYS_TRANSITION_IN_PROGRESS
	// This state is mandatory for multicore systems where tasks executing on other cores
	// than the one performing the transition may be executed concurrently
	OldState = SysState;
	SysState = SYS_TRANSITION_IN_PROGRESS;
        
	// Call corresponding components callbacks register on "State" transition
	for (i=0; i<SysStatesNbCallbacks[State]; i++)
        //for (i=0; i <= SysStatesNbCallbacks[State]; i++)
	{
		if (pSysStatesFunc[State][i] != NULL)
		{
			(pSysStatesFunc[State][i])(OldState,State);
		}
	}
	
	// Now we can update the system state
	SysState = State;

	// Release mutual exclusion
	//Preetha - TestCode
        //semGive(SemSysStateTransition);        
        KS_CloseSema(SemSysStateTransitionQ);         
        
	
	// Restoring back priority of the calling task
	//taskPrioritySet(0, Prio);
        
        //Preetha - TestCode
        KS_DefTaskPriority(0, Prio);        
}



/*! 
 * \fn void SYS_RegisterStateTransitionCallback(SYS_STATE_TRANSITION_FCT pFunc, E_SYS_STATE State, int Rank)
 * \brief Function used by components of the system to register a callback that will be called on a System State transition.
 *
 * \param pFunc: the function to be registered. Must be defined as "void pFunc(E_SYS_STATE FromState, E_SYS_STATE ToState)"
 * \param State: pFunc will be called within the transition to State
 * \param Rank: the rank of execution of pFunc when transition to State is executed (see enums XXX_RANK_CALLBACK in SysManagerAdaptation.h)
 */
void SYS_RegisterStateTransitionCallback(SYS_STATE_TRANSITION_FCT pFunc, E_SYS_STATE State, int Rank)
{
	if ((pSysStatesFunc[State] != NULL) && (Rank < SysStatesNbCallbacks[State]))
	{
		// Should always be the case as long as State is a valid E_SYS_STATE (ie <SYS_NB_STATES) and Rank is a valid State_RANK_CALLBACK
		// Register pFunc in the corresponding slot
		pSysStatesFunc[State][Rank] = pFunc;
	}
}


/*! 
 * \fn E_SYS_STATE SYS_GetState(void)
 * \brief Function that returns the System State
 *
 */
E_SYS_STATE SYS_GetState(void)
{
	return SysState;
}


/*! 
 * \fn static void SysHookTasksCreation(TASK_ID tid)
 * \brief Function that will be called within task creation. It adjust core affinity and priority if the task is part of SYSADAPT_SystemTasks.
 *
 * \param tid: TASK_ID of the task being spawned
 */
static void SysHookTasksCreation(TASK tid)
{
	int i;
	char *NameOfTask;
	int bFinished = FALSE;
	//cpuset_t cpu; --> Preetha : Verify if there is an equivalent API in RTXC ??
	
	// Get the name of the task being spawned
	//NameOfTask = taskName(tid);
        
        //Preetha - TestCode   
        NameOfTask = KS_GetTaskName (tid);
	
	// Find if it belongs to our system tasks
	i = 0;
	do
	{
		if (strcmp(SYSADAPT_SystemTasks[i].name, "") == 0) 
		{
			// All the task array has been scanned => go out of the loop
			bFinished = TRUE;
		}
		else if (strcmp(SYSADAPT_SystemTasks[i].name, NameOfTask) == 0) 
		{
#ifdef _WRS_VX_SMP
		//--> Preetha : Commented this out ..Verify if there is an equivalent API in RTXC ??	
                  // Set core affinity of the tasks if asked
			/*if (SYSADAPT_SystemTasks[i].core != E_NO_CPU_AFFINITY)
			{
				CPUSET_ZERO(cpu);
				CPUSET_SET(cpu, SYSADAPT_SystemTasks[i].core);
				taskCpuAffinitySet(tid, cpu);
			}*/
#endif // _WRS_VX_SMP
			
			//Preetha - Set priority of the task
			//taskPrioritySet(tid, SYSADAPT_SystemTasks[i].priority);
                        KS_DefTaskPriority(tid, SYSADAPT_SystemTasks[i].priority);
                                                

			// We found the task => go out of the loop
			bFinished = TRUE;
		}
		i++;
		
	} while (!bFinished);
}

