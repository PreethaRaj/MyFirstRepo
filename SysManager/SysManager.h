/*!
 * \file  SysManager.h
 * \brief Interfaces of the whole SysManager (including component manager)
 */

#ifndef SYSMANAGER_H
#define SYSMANAGER_H

#include "SysMgrAdapt/SysMgrAdapt.h"
#include "SysMgrCmp.h"	

//Preetha
#include "rtxcapi.h" /* RTXC Kernel Service prototypes */
//#include "taskLib.h"
#include "ktask.h" /* defines TASKA */
#include "ksema.h" /* defines GOSEMA */
#include "kcounter.h" /* defines COUNTER1 */
#include "kproject.h" /* defines CLKTICK */


#define FALSE		0
#define TRUE		1

/*! 
 * \typedef SYS_STATE_TRANSITION_FCT
 * \brief format of the callback functions
 *
 */
typedef void (*SYS_STATE_TRANSITION_FCT)(E_SYS_STATE, E_SYS_STATE);

// Interface functions
void SYS_Init(void);
E_SYS_STATE SYS_GetState(void);
//Preetha
//void SYS_LockStateTransition(void);
KSRC SYS_LockStateTransition(const char *pname);

void SYS_UnlockStateTransition(void);
void SYS_StateTransition(E_SYS_STATE State);
void SYS_RegisterStateTransitionCallback(SYS_STATE_TRANSITION_FCT pFunc, E_SYS_STATE State, int Rank);
void SYS_FatalError(const char *pLogstring); // Can be adapted (implemented in SysMgrAdapt.c)

#endif  // SYSMANAGER_H
