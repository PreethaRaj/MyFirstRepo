/*!
 * \file SysMgrAdapt.c
 * \brief System Manager adaptation layer
 *
 * Search for "SYSMGR_ADAPTATION" to see where are the adaptations that can be done to fit to your platform
 * [SYSMGR_ADAPTATION begin]
 * This file allows to define all tasks of your system with their core affinity and priority (see SYSADAPT_SystemTasks)
 * It provides also the system Manager adaptation interfaces needed by SysManager.c:
 * - SYSADAPT_CallComponentsHook
 * - SYSADAPT_GetNbCallbacks
 * [SYSMGR_ADAPTATION end]
 * 
 */

#include "SysMgrAdapt.h"
#include "SysMgrAdaptPriv.h"
//#include "CmpExample.h"	// [ADD_A_COMPONENT]:add .h of component you want to include
   //Preetha
#include "../../CmpExample/CmpExample.h"
#include <stdio.h>


/*! 
 * \var SYSTEM_TASK SYSADAPT_SystemTasks[]   
 * \brief Array containing all system tasks with their core affinity and priority 
 *
 * All tasks defined in this array will have their core affinity and priority updated accordingly
 * at creation time. This allows to have a clear view of all system tasks and to be able to change
 * core affinity / priority of tasks of third parties components (that can even be used as binary components)
 * [SYSMGR_ADAPTATION begin]: following rules must be followed:
 * 1) All tasks defined here must have lower priority than SYS_MGR_TASK_PRIO (exception can be tasks that do not read nor set SysState)
 * on multicore system, core affinity can be chosen freely
 * [SYSMGR_ADAPTATION end]
 */
SYSTEM_TASK SYSADAPT_SystemTasks[] = 
{
	{"ExampleTask", 	E_CPU_AFFINITY_CORE0, 		100},   // [ADD_A_COMPONENT] : add the priority of your components tasks (if any)
	//{"Example1Task", 	E_CPU_AFFINITY_CORE1, 		101},   // [ADD_A_COMPONENT] : add the priority of your components tasks (if any)
	{"CmpMgrTask", 		E_CPU_AFFINITY_CORE0, 		102},  // Low priority task that manage component live cycle
	{"", E_NO_CPU_AFFINITY, 0}	// End array identifier => do not change, keep at the end of the array
		
};

/*! 
 * \var E_SYS_STATE SYSADAPT_InitialState   
 * \brief [SYSMGR_ADAPTATION]: just set this variable to the initial state of the system
 *
 */
E_SYS_STATE SYSADAPT_InitialState = SYS_NO_CONF;

/*! 
 * \fn void SYSADAPT_CallComponentsHook(E_CMP_HOOKS Hook)   
 * \brief Execute Hook of each component of the system   
 *
 * \param Hook that will be executed (see E_CMP_HOOKS)
 */
void SYSADAPT_CallComponentsHook(E_CMP_HOOKS Hook)
{
	// [ADD_A_COMPONENT]
	// Add the call to your CmpX
	// Use the different hooks (see E_CMP_HOOKS) to perform
	// actions before or after the ones of another component

	//May be, here we need to add something like a switch case to take action for each hook
	// or simply call CmpExample(E_CMP_HOOKS hook), which does various actions for various hooks
		
	if (CmpExample(Hook) == HOOK_CALL_FATALERROR)
	{
		// Fatal error
		SYS_FatalError("SysManager: CmpExample fatal error\n");
	}
	
	//if (CmpExample1(Hook) == HOOK_CALL_FATALERROR)
	//{
		//// Fatal error
		//SYS_FatalError("SysManager: CmpExample1 fatal error\n");
	//}
}


/*! 
 * \fn unsigned int SYSADAPT_GetNbCallbacks(E_SYS_STATE State)  
 * \brief Return the number of callbacks associated to State  
 *
 * \param State
 * \return NbCallbacks associated to State transition
 */
unsigned int SYSADAPT_GetNbCallbacks(E_SYS_STATE State)
{
	int NbCallbacks = 0;
	
	switch (State)
	{
	case SYS_NO_CONF:
		NbCallbacks = NOCONF_NB_CALLBACKS;
		break;
	case SYS_CONFIGURING:
		NbCallbacks = CONFIGURING_NB_CALLBACKS;
		break;
	case SYS_CONFIGURED:
		NbCallbacks = CONFIGURED_NB_CALLBACKS;
		break;
	case SYS_FATAL_ERROR:
		NbCallbacks = FATALERROR_NB_CALLBACKS;
		break;
	default:
		break;
	}
	
	return NbCallbacks;
}


/*! 
 * \fn void SYS_FatalError(const char *pLogstring)  
 * \brief Function to be used when a fatal error is detected
 *
 * This function can be adapted, for example to log the fatal error in a file
 * and/or to switch to particular state ...
 *
 * \param pLogstring string describing the error
 */
void SYS_FatalError(const char *pLogstring)
{
	printf(pLogstring);
	while (1);
}
