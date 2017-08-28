/*!
 * \file  SysMgrAdapt.h
 * \brief Adaptation of SysManager component
 * 
 * Search for "SYSMGR_ADAPTATION" to see where are the adaptations that can be done to fit to your platform
 * 
 */

#ifndef SYSMGRADAPT_H
#define SYSMGRADAPT_H


/*! 
 * \def CMP_MGR_STACK_SIZE
 * \brief Size of CmpMgrTask
 * 
 * [SYSMGR_ADAPTATION] might be adapted if needed 
 * (increased if stack overflow, decreased if memory saving has to be done)
 */
#define CMP_MGR_STACK_SIZE	2048


/*! 
 * \def CMP_CYCLE_PERIOD_IN_MS
 * \brief Period of CMP_CYCLE components hook calls by CmpMgrTask
 * 
 * [SYSMGR_ADAPTATION] might be adapted if needed 
 */
#define CMP_CYCLE_PERIOD_IN_MS	50


/*********************** System State ***************************/

/*! 
 * \enum E_SYS_STATE
 * \brief Define all possible states of the system
 *
 * [SYSMGR_ADAPTATION begin] Depending on the system some states can be added or removed.
 * Below is just an example of the possible system states.
 * Anyway, the following rules must be followed:
 * 1) The first state is always 0 and the others follow one by one
 * 2) SYS_NB_STATES must always be the before last item
 * 3) SYS_TRANSITION_IN_PROGRESS must always be the last item and must not be used as input of SYS_StateTransition()
 * [SYSMGR_ADAPTATION end]
 * 
 */
typedef enum
{
    SYS_NO_CONF = 0,		// There isn't a valid configuration
    SYS_CONFIGURING,		// Configuration is being written on the system
    SYS_CONFIGURED,			// Configuration is OK
    SYS_FATAL_ERROR,		// Fatal error => reboot will be performed 
	SYS_NB_STATES,			// Number of states (keep as before last item)
	SYS_TRANSITION_IN_PROGRESS  // Used as temporary state when transition is in progress (keep as last item)
} E_SYS_STATE;



/*! 
 * \enum E_SYS_NOCONF_RANK_CALLS
 * \brief Define the order for callbacks on SYS_NOCONF state transition
 *
 * Must be defined all together by firmware team
 */
typedef enum
{ 
    NOCONF_EXAMPLE_RANK_CALLBACK = 0,
    //NOCONF_EXAMPLE1_RANK_CALLBACK,
    NOCONF_NB_CALLBACKS
} E_SYS_NOCONF_RANK_CALLS;


/*! 
 * \def CONFIGURING_NB_CALLBACKS
 * \brief Define the order for callbacks on SYS_CONFIGURING state transition
 *
 * Must be defined all together by firmware team. No callback for this state => define as 0
 */
#define CONFIGURING_NB_CALLBACKS	0

/*! 
 * \enum E_SYS_CONFIGURED_RANK_CALLS
 * \brief Define the order for callbacks on SYS_CONFIGURED state transition
 *
 * Must be defined all together by firmware team
 */
typedef enum
{ 
    CONFIGURED_EXAMPLE_RANK_CALLBACK = 0,
    //CONFIGURED_EXAMPLE1_RANK_CALLBACK,
    CONFIGURED_NB_CALLBACKS
} E_SYS_CONFIGURED_RANK_CALLS;


/*! 
 * \enum E_SYS_FATALERROR_RANK_CALLS
 * \brief Define the order for callbacks on SYS_FATAL_ERROR state transition
 *
 * Must be defined all together by firmware team
 */
typedef enum
{ 
    FATALERROR_EXAMPLE_RANK_CALLBACK = 0,
    //FATALERROR_EXAMPLE1_RANK_CALLBACK,
    FATALERROR_NB_CALLBACKS
} E_SYS_FATALERROR_RANK_CALLS;

/*********************** end System State ***************************/


#endif  // SYSMGRADAPT_H
