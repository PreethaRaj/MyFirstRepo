/*!
 * \file  SysMgrAdaptPriv.h
 * \brief Private interfaces of SysManager adaptation. Needed by SysManager but not exported to the outside
 * 
 */

#ifndef SYSMGRADAPTPRIV_H
#define SYSMGRADAPTPRIV_H

#include "SysMgrAdapt.h"
//#include "SysMgrCmp.h"
   //Preetha
#include "../SysManager/SysMgrCmp.h"

#define SYS_MGR_TASK_PRIO	10

/*! 
 * \enum E_CPU_AFFINITY
 * \brief Define core affinity for multicore platforms
 *
 * Define the core affinity available for a sytem task (ie defined in SYSADAPT_SystemTasks)
 * Setting core affinity to E_NO_CPU_AFFINITY will enable "load balancing" on the specified task
 * 
 * [SYSMGR_ADAPTATION] If the platform has more than 2 cores, adapt enum accordingly
 * 
 */
typedef enum
{
	E_NO_CPU_AFFINITY = -1,
	E_CPU_AFFINITY_CORE0 = 0,
	E_CPU_AFFINITY_CORE1
} E_CPU_AFFINITY;


/*! 
 * \struct SYSTEM_TASK
 * \brief Define a system task entry in SYSADAPT_SystemTasks
 * 
 */
typedef struct
{
	char* name;
	E_CPU_AFFINITY core;
	int priority;
} SYSTEM_TASK;


void SYSADAPT_CallComponentsHook(E_CMP_HOOKS Hook);
unsigned int SYSADAPT_GetNbCallbacks(E_SYS_STATE State);

extern SYSTEM_TASK SYSADAPT_SystemTasks[];
extern E_SYS_STATE SYSADAPT_InitialState;

#endif  // SYSMGRADAPTPRIV_H
